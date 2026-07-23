"""Patient schemas."""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class PatientCreate(BaseModel):
    """Payload for registering a patient."""

    user_id: str | None = None
    medical_record_number: str = Field(min_length=2, max_length=50)
    full_name: str = Field(min_length=2, max_length=150)
    date_of_birth: date | None = None
    gender: str | None = Field(default=None, max_length=30)
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = None


class PatientUpdate(BaseModel):
    """Fields that can be modified for a patient."""

    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    date_of_birth: date | None = None
    gender: str | None = Field(default=None, max_length=30)
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = None


class PatientRead(PatientCreate):
    """Patient returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
