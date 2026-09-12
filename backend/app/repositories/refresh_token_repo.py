from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken


def create(db: Session, *, user_id, jti: str, token_hash: str, expires_at: datetime) -> RefreshToken:
    rt = RefreshToken(user_id=user_id, jti=jti, token_hash=token_hash, expires_at=expires_at)
    db.add(rt)
    db.flush()
    return rt


def get_by_jti(db: Session, jti: str) -> RefreshToken | None:
    return db.scalar(select(RefreshToken).where(RefreshToken.jti == jti))


def revoke(db: Session, rt: RefreshToken) -> None:
    rt.revoked = True
    db.flush()


def revoke_all_for_user(db: Session, user_id) -> None:
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False))
        .values(revoked=True)
    )
    db.flush()
