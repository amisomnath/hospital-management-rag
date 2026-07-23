"""User endpoints."""

from fastapi import APIRouter

from app.api.deps import CurrentUser, DatabaseSession
from app.crud.user import list_users
from app.models.user import User
from app.schemas.user import UserRead

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserRead)
def read_me(current_user: CurrentUser) -> User:
    """Return the authenticated user."""

    return current_user


@router.get("", response_model=list[UserRead])
def read_users(db: DatabaseSession, _: CurrentUser) -> list[User]:
    """List users. A real deployment should restrict this to admins."""

    return list_users(db)
