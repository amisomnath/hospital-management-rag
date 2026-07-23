"""Patient endpoints."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.api.deps import DatabaseSession
from app.crud.patient import (
    create_patient,
    get_patient,
    list_patients,
    update_patient,
)
from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientRead, PatientUpdate

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.post("", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
def add_patient(payload: PatientCreate, db: DatabaseSession) -> Patient:
    """Register a patient."""

    try:
        return create_patient(db, payload)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Medical record number or user profile already exists",
        ) from None


@router.get("", response_model=list[PatientRead])
def read_patients(db: DatabaseSession) -> list[Patient]:
    """List registered patients."""

    return list_patients(db)


@router.get("/{patient_id}", response_model=PatientRead)
def read_patient(patient_id: str, db: DatabaseSession) -> Patient:
    """Return one patient."""

    patient = get_patient(db, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.patch("/{patient_id}", response_model=PatientRead)
def edit_patient(
    patient_id: str, payload: PatientUpdate, db: DatabaseSession
) -> Patient:
    """Update one patient."""

    patient = get_patient(db, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return update_patient(db, patient, payload)
