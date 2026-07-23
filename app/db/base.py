"""SQLAlchemy declarative base and model registration."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class inherited by every SQLAlchemy model."""


# Import models after Base exists so Alembic can discover all tables.
from app import models as _models  # noqa: E402,F401
