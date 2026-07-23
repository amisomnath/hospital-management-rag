"""Department schemas."""

from pydantic import BaseModel, ConfigDict, Field


class DepartmentCreate(BaseModel):
    """Payload for creating a hospital department."""

    name: str = Field(min_length=2, max_length=120)
    description: str | None = None


class DepartmentRead(DepartmentCreate):
    """Department returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
