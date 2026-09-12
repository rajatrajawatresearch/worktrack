from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import UserStatus
from app.models.user import User


def get(db: Session, user_id) -> User | None:
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower().strip()))


def create(
    db: Session,
    *,
    email: str,
    password_hash: str,
    role: str,
    company_id=None,
    phone: str | None = None,
    status: str = UserStatus.ACTIVE,
) -> User:
    user = User(
        email=email.lower().strip(),
        password_hash=password_hash,
        role=role,
        company_id=company_id,
        phone=phone,
        status=status,
    )
    db.add(user)
    db.flush()
    return user
