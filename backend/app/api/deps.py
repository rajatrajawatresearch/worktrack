"""Shared FastAPI dependencies: authentication, RBAC, tenant scoping."""

import uuid
from typing import Annotated

import jwt
from fastapi import Depends, Header, Query, Request
from sqlalchemy.orm import Session

from app.core import security
from app.core.database import get_db
from app.core.enums import CompanyStatus, Role, UserStatus
from app.core.errors import forbidden, unauthorized
from app.models.company import Company
from app.models.employee import Employee
from app.models.user import User
from app.repositories import company_repo, employee_repo, user_repo


def get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def get_current_user(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise unauthorized("Missing authentication token.")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = security.decode_token(token)
    except jwt.PyJWTError as exc:
        raise unauthorized("Invalid or expired token.") from exc
    if payload.get("type") != "access":
        raise unauthorized("Invalid token type.")
    try:
        user_id = uuid.UUID(str(payload.get("sub")))
    except (ValueError, TypeError) as exc:
        raise unauthorized("Invalid token subject.") from exc

    user = user_repo.get(db, user_id)
    if not user or user.status != UserStatus.ACTIVE:
        raise unauthorized("Account not found or inactive.")
    request.state.user = user
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: str):
    def _dep(user: CurrentUser) -> User:
        if user.role not in roles:
            raise forbidden()
        return user

    return _dep


def require_admin(user: CurrentUser) -> User:
    if user.role not in Role.ADMINS:
        raise forbidden()
    return user


def require_super_admin(user: CurrentUser) -> User:
    if user.role != Role.SUPER_ADMIN:
        raise forbidden()
    return user


def get_employee_context(
    user: CurrentUser, db: Session = Depends(get_db)
) -> tuple[Employee, Company]:
    if user.role != Role.EMPLOYEE:
        raise forbidden("This action is only available to employees.")
    emp = employee_repo.get_by_user(db, user.id)
    if not emp:
        raise forbidden("No employee profile is linked to this account.")
    company = company_repo.get(db, emp.company_id)
    if not company or company.status != CompanyStatus.ACTIVE:
        raise forbidden("Your company is not active. Contact your administrator.")
    return emp, company


def company_scope(
    user: Annotated[User, Depends(require_admin)],
    company_id: Annotated[uuid.UUID | None, Query()] = None,
) -> tuple[User, uuid.UUID | None]:
    """Resolve the effective company scope for admin endpoints.

    COMPANY_ADMIN is always locked to their own company (client-supplied
    company_id is ignored). SUPER_ADMIN may optionally filter by company_id;
    None means "all companies".
    """
    if user.role == Role.COMPANY_ADMIN:
        return user, user.company_id
    return user, company_id


def pagination(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> tuple[int, int]:
    return page, page_size


AdminScope = Annotated[tuple[User, uuid.UUID | None], Depends(company_scope)]
EmployeeContext = Annotated[tuple[Employee, Company], Depends(get_employee_context)]
Pagination = Annotated[tuple[int, int], Depends(pagination)]
