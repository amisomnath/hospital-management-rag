"""Department CRUD functions."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.department import Department
from app.schemas.department import DepartmentCreate


def create_department(db: Session, payload: DepartmentCreate) -> Department:
    """Create a hospital department."""

    department = Department(**payload.model_dump())
    db.add(department)
    db.commit()
    db.refresh(department)
    return department


def get_department(db: Session, department_id: str) -> Department | None:
    """Return a department by ID."""

    return db.get(Department, department_id)


def list_departments(db: Session) -> list[Department]:
    """Return all departments alphabetically."""

    return list(db.scalars(select(Department).order_by(Department.name)).all())
