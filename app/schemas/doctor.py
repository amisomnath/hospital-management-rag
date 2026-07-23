"""Doctor schemas."""

from pydantic import BaseModel, ConfigDict, Field


class DoctorCreate(BaseModel):
    """Payload for creating a doctor profile."""

    user_id: str | None = None
    department_id: str | None = None
    full_name: str = Field(min_length=2, max_length=150)
    specialization: str = Field(min_length=2, max_length=150)
    license_number: str = Field(min_length=2, max_length=80)
    is_available: bool = True


class DoctorUpdate(BaseModel):
    """Fields that can be updated for a doctor."""

    department_id: str | None = None
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    specialization: str | None = Field(default=None, min_length=2, max_length=150)
    is_available: bool | None = None


class DoctorRead(DoctorCreate):
    """Doctor returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
