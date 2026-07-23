"""Version 1 API router aggregation."""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.api.v1.endpoints import (
    appointments,
    auth,
    chat,
    departments,
    doctors,
    documents,
    health,
    patients,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
authenticated = [Depends(get_current_user)]
api_router.include_router(patients.router, dependencies=authenticated)
api_router.include_router(doctors.router, dependencies=authenticated)
api_router.include_router(departments.router, dependencies=authenticated)
api_router.include_router(appointments.router, dependencies=authenticated)
api_router.include_router(documents.router)
api_router.include_router(chat.router)
api_router.include_router(health.router)
