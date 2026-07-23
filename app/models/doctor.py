"""Doctor database model."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.appointment import Appointment
    from app.models.department import Department
    from app.models.user import User


class Doctor(Base):
    """Doctor profile and department membership."""

    __tablename__ = "doctors"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), unique=True, nullable=True
    )
    department_id: Mapped[str | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    full_name: Mapped[str] = mapped_column(String(150), index=True)
    specialization: Mapped[str] = mapped_column(String(150), index=True)
    license_number: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["User | None"] = relationship(back_populates="doctor_profile")
    department: Mapped["Department | None"] = relationship(back_populates="doctors")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="doctor")
