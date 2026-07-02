"""v1 API router aggregation."""
from fastapi import APIRouter

from app.api.v1 import (
    admin,
    admissions,
    auth,
    chat,
    checkins,
    dashboard,
    escalations,
    outcomes,
    patients,
    predictions,
    reports,
    transitions,
    webhooks,
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
api_router.include_router(transitions.router)
api_router.include_router(checkins.router)
api_router.include_router(escalations.router)
api_router.include_router(outcomes.router)
api_router.include_router(webhooks.router)
