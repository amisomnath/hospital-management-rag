"""Appointment CRUD functions."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate


def create_appointment(db: Session, payload: AppointmentCreate) -> Appointment:
    """Book an appointment."""

    appointment = Appointment(**payload.model_dump())
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def get_appointment(db: Session, appointment_id: str) -> Appointment | None:
    """Return an appointment by ID."""

    return db.get(Appointment, appointment_id)


def list_appointments(
    db: Session, patient_id: str | None = None, doctor_id: str | None = None
) -> list[Appointment]:
    """Return appointments with optional patient/doctor filters."""

    statement = select(Appointment)
    if patient_id:
        statement = statement.where(Appointment.patient_id == patient_id)
    if doctor_id:
        statement = statement.where(Appointment.doctor_id == doctor_id)
    statement = statement.order_by(Appointment.scheduled_at)
    return list(db.scalars(statement).all())


def update_appointment(
    db: Session, appointment: Appointment, payload: AppointmentUpdate
) -> Appointment:
    """Update appointment status, time or notes."""

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(appointment, field, value)
    db.commit()
    db.refresh(appointment)
    return appointment
