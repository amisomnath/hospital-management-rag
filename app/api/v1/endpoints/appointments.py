"""Appointment endpoints."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.api.deps import DatabaseSession
from app.crud.appointment import (
    create_appointment,
    get_appointment,
    list_appointments,
    update_appointment,
)
from app.models.appointment import Appointment
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentRead,
    AppointmentUpdate,
)

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.post("", response_model=AppointmentRead, status_code=status.HTTP_201_CREATED)
def book_appointment(payload: AppointmentCreate, db: DatabaseSession) -> Appointment:
    """Book a patient with a doctor."""

    try:
        return create_appointment(db, payload)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient or doctor does not exist",
        ) from None


@router.get("", response_model=list[AppointmentRead])
def read_appointments(
    db: DatabaseSession,
    patient_id: str | None = None,
    doctor_id: str | None = None,
) -> list[Appointment]:
    """List appointments with optional filters."""

    return list_appointments(db, patient_id, doctor_id)


@router.patch("/{appointment_id}", response_model=AppointmentRead)
def edit_appointment(
    appointment_id: str, payload: AppointmentUpdate, db: DatabaseSession
) -> Appointment:
    """Update an appointment."""

    appointment = get_appointment(db, appointment_id)
    if appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return update_appointment(db, appointment, payload)
