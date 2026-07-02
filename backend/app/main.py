"""FastAPI entry point."""
from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.services import followup_service
from app.services.messaging import get_provider
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.db.base import Base
from app.db.seed import seed_all
from app.db.session import SessionLocal, engine
from app.middleware.audit import AuditMiddleware
import app.models  # noqa: F401 — ensure model registration with Base.metadata

logger = get_logger(__name__)


def _followup_tick() -> None:
    db = SessionLocal()
    try:
        followup_service.run_cycle(db, get_provider(), now=datetime.now(timezone.utc))
    except Exception as exc:  # noqa: BLE001 - a failed tick must not kill the scheduler
        logger.warning("Follow-up cycle failed: %s", exc)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    # For SQLite dev mode, create tables directly. Postgres uses Alembic.
    if settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
        logger.info("SQLite dev DB ready at %s", settings.database_url)
    if settings.seed_demo_data:
        db = SessionLocal()
        try:
            seed_all(db)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Seed skipped: %s", exc)
        finally:
            db.close()
    scheduler = BackgroundScheduler()
    scheduler.add_job(_followup_tick, "interval", minutes=2, id="followup-cycle")
    scheduler.start()
    logger.info("Follow-up scheduler started (provider=%s)", settings.messaging_provider)
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuditMiddleware)
app.include_router(api_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/meta")
def meta() -> dict[str, str]:
    return {"app": settings.app_name, "messaging_mode": settings.messaging_provider}
