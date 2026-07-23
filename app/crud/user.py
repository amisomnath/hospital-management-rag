"""User CRUD functions."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.schemas.auth import RegisterRequest


def get_user(db: Session, user_id: str) -> User | None:
    """Return a user by primary key."""

    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    """Return a user by case-insensitive email."""

    statement = select(User).where(User.email == email.lower())
    return db.scalar(statement)


def list_users(db: Session, offset: int = 0, limit: int = 100) -> list[User]:
    """Return a paginated user list."""

    statement = select(User).offset(offset).limit(limit).order_by(User.created_at)
    return list(db.scalars(statement).all())


def create_user(db: Session, payload: RegisterRequest) -> User:
    """Create and persist a user."""

    user = User(
        email=str(payload.email).lower(),
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
