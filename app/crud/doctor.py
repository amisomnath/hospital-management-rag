"""Doctor CRUD functions."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.doctor import Doctor
from app.schemas.doctor import DoctorCreate, DoctorUpdate


def create_doctor(db: Session, payload: DoctorCreate) -> Doctor:
    """Create a doctor profile."""

    doctor = Doctor(**payload.model_dump())
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


def get_doctor(db: Session, doctor_id: str) -> Doctor | None:
    """Return a doctor by ID."""

    return db.get(Doctor, doctor_id)


def list_doctors(db: Session, department_id: str | None = None) -> list[Doctor]:
    """Return doctors, optionally filtered by department."""

    statement = select(Doctor)
    if department_id:
        statement = statement.where(Doctor.department_id == department_id)
    return list(db.scalars(statement.order_by(Doctor.full_name)).all())


def update_doctor(db: Session, doctor: Doctor, payload: DoctorUpdate) -> Doctor:
    """Update a doctor profile."""

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(doctor, field, value)
    db.commit()
    db.refresh(doctor)
    return doctor
