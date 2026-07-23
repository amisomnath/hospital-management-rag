"""Appointment schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AppointmentCreate(BaseModel):
    """Payload for booking an appointment."""

    patient_id: str
    doctor_id: str
    scheduled_at: datetime
    reason: str = Field(min_length=3)
    notes: str | None = None


class AppointmentUpdate(BaseModel):
    """Appointment fields that can change."""

    scheduled_at: datetime | None = None
    status: str | None = Field(default=None, max_length=30)
    notes: str | None = None


class AppointmentRead(AppointmentCreate):
    """Appointment returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
