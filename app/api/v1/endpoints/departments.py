"""Department endpoints."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.api.deps import DatabaseSession
from app.crud.department import create_department, list_departments
from app.models.department import Department
from app.schemas.department import DepartmentCreate, DepartmentRead

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.post("", response_model=DepartmentRead, status_code=status.HTTP_201_CREATED)
def add_department(payload: DepartmentCreate, db: DatabaseSession) -> Department:
    """Create a hospital department."""

    try:
        return create_department(db, payload)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A department with this name already exists",
        ) from None


@router.get("", response_model=list[DepartmentRead])
def read_departments(db: DatabaseSession) -> list[Department]:
    """List hospital departments."""

    return list_departments(db)
