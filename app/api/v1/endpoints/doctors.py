"""Doctor endpoints."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.api.deps import DatabaseSession
from app.crud.doctor import create_doctor, get_doctor, list_doctors, update_doctor
from app.models.doctor import Doctor
from app.schemas.doctor import DoctorCreate, DoctorRead, DoctorUpdate

router = APIRouter(prefix="/doctors", tags=["Doctors"])


@router.post("", response_model=DoctorRead, status_code=status.HTTP_201_CREATED)
def add_doctor(payload: DoctorCreate, db: DatabaseSession) -> Doctor:
    """Create a doctor profile."""

    try:
        return create_doctor(db, payload)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Doctor licence or linked user already exists",
        ) from None


@router.get("", response_model=list[DoctorRead])
def read_doctors(db: DatabaseSession, department_id: str | None = None) -> list[Doctor]:
    """List doctors, optionally within one department."""

    return list_doctors(db, department_id)


@router.get("/{doctor_id}", response_model=DoctorRead)
def read_doctor(doctor_id: str, db: DatabaseSession) -> Doctor:
    """Return one doctor."""

    doctor = get_doctor(db, doctor_id)
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor


@router.patch("/{doctor_id}", response_model=DoctorRead)
def edit_doctor(doctor_id: str, payload: DoctorUpdate, db: DatabaseSession) -> Doctor:
    """Update a doctor profile."""

    doctor = get_doctor(db, doctor_id)
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return update_doctor(db, doctor, payload)
