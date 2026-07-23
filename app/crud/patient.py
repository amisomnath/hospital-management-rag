"""Patient CRUD functions."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientUpdate


def create_patient(db: Session, payload: PatientCreate) -> Patient:
    """Create a patient record."""

    patient = Patient(**payload.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def get_patient(db: Session, patient_id: str) -> Patient | None:
    """Return a patient by ID."""

    return db.get(Patient, patient_id)


def list_patients(db: Session, offset: int = 0, limit: int = 100) -> list[Patient]:
    """Return patients ordered by name."""

    statement = select(Patient).offset(offset).limit(limit).order_by(Patient.full_name)
    return list(db.scalars(statement).all())


def update_patient(db: Session, patient: Patient, payload: PatientUpdate) -> Patient:
    """Apply provided fields to an existing patient."""

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(patient, field, value)
    db.commit()
    db.refresh(patient)
    return patient
