"""Authentication business logic: login, token rotation, logout, /me context."""

from datetime import UTC

import jwt
from sqlalchemy.orm import Session

from app.core import security
from app.core.enums import AuditAction, Role, UserStatus
from app.core.errors import forbidden, unauthorized
from app.models.user import User
from app.repositories import (
    audit_repo,
    company_repo,
    employee_repo,
    refresh_token_repo,
    user_repo,
)


def authenticate(db: Session, email: str, password: str) -> User:
    user = user_repo.get_by_email(db, email)
    # Verify against a hash even when the user is missing is nice-to-have; here we
    # simply reject with the same generic message to avoid user enumeration.
    if not user or not security.verify_password(password, user.password_hash):
        raise unauthorized("Invalid email or password.", code="INVALID_CREDENTIALS")
    if user.status != UserStatus.ACTIVE:
        raise forbidden("Your account is inactive. Please contact your administrator.")
    return user


def issue_tokens(db: Session, user: User) -> tuple[str, str]:
    access = security.create_access_token(user.id, user.role, user.company_id)
    refresh, jti, expires_at = security.create_refresh_token(user.id, user.role, user.company_id)
    refresh_token_repo.create(
        db,
        user_id=user.id,
        jti=jti,
        token_hash=security.hash_token(refresh),
        expires_at=expires_at,
    )
    return access, refresh


def login(db: Session, email: str, password: str, ip: str | None = None) -> tuple[User, str, str]:
    user = authenticate(db, email, password)
    user.last_login_at = security.utcnow()
    access, refresh = issue_tokens(db, user)
    audit_repo.create(
        db, action=AuditAction.LOGIN, user_id=user.id, company_id=user.company_id, ip_address=ip
    )
    return user, access, refresh


def refresh_tokens(db: Session, refresh_token: str) -> tuple[str, str]:
    try:
        payload = security.decode_token(refresh_token)
    except jwt.PyJWTError as exc:
        raise unauthorized(
            "Invalid or expired refresh token.", code="INVALID_REFRESH_TOKEN"
        ) from exc
    if payload.get("type") != "refresh":
        raise unauthorized("Invalid refresh token.", code="INVALID_REFRESH_TOKEN")

    rt = refresh_token_repo.get_by_jti(db, payload.get("jti", ""))
    if not rt or rt.revoked or rt.token_hash != security.hash_token(refresh_token):
        raise unauthorized("Invalid or expired refresh token.", code="INVALID_REFRESH_TOKEN")

    expires_at = rt.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at < security.utcnow():
        raise unauthorized("Invalid or expired refresh token.", code="INVALID_REFRESH_TOKEN")

    user = user_repo.get(db, rt.user_id)
    if not user or user.status != UserStatus.ACTIVE:
        raise unauthorized("Invalid or expired refresh token.", code="INVALID_REFRESH_TOKEN")

    # Rotate: revoke the presented token and issue a fresh pair.
    refresh_token_repo.revoke(db, rt)
    return issue_tokens(db, user)


def logout(db: Session, refresh_token: str, user: User) -> bool:
    try:
        payload = security.decode_token(refresh_token)
        rt = refresh_token_repo.get_by_jti(db, payload.get("jti", ""))
        if rt and not rt.revoked and rt.user_id == user.id:
            refresh_token_repo.revoke(db, rt)
    except jwt.PyJWTError:
        pass  # logout is idempotent; never leak token validity
    audit_repo.create(
        db, action=AuditAction.LOGOUT, user_id=user.id, company_id=user.company_id
    )
    return True


def build_me(db: Session, user: User):
    employee = employee_repo.get_by_user(db, user.id) if user.role == Role.EMPLOYEE else None
    company = company_repo.get(db, user.company_id) if user.company_id else None
    return user, employee, company
