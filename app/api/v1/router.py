"""Version 1 API router aggregation."""

from fastapi import APIRouter

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
api_router.include_router(patients.router)
api_router.include_router(doctors.router)
api_router.include_router(departments.router)
api_router.include_router(appointments.router)
api_router.include_router(documents.router)
api_router.include_router(chat.router)
api_router.include_router(health.router)
