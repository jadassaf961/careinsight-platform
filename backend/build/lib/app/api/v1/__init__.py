"""v1 API router aggregation."""
from fastapi import APIRouter

from app.api.v1 import (
    admin,
    admissions,
    auth,
    chat,
    dashboard,
    patients,
    predictions,
    reports,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(patients.router)
api_router.include_router(admissions.router)
api_router.include_router(predictions.router)
api_router.include_router(reports.router)
api_router.include_router(chat.router)
api_router.include_router(dashboard.router)
api_router.include_router(admin.router)
