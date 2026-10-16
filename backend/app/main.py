import logging

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import APP_NAME, APP_VERSION, CORS_ORIGINS
from app.database import get_db
from app.routers import appointments, doctors, patients, stats

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Appointment management API for a small multi-doctor clinic.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(doctors.router)
app.include_router(patients.router)
app.include_router(appointments.router)
app.include_router(stats.router)

# request count / latency histograms for prometheus, served on /metrics
Instrumentator(excluded_handlers=["/metrics", "/health", "/ready"]).instrument(app).expose(
    app, include_in_schema=False
)


@app.get("/", tags=["system"])
def root():
    return {"service": APP_NAME, "version": APP_VERSION, "docs": "/docs"}


@app.get("/health", tags=["system"])
def health():
    # liveness: the process is up and serving requests
    return {"status": "UP"}


@app.get("/ready", tags=["system"])
def ready(db: Session = Depends(get_db)):
    # readiness: only take traffic when the database answers
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(status_code=503, detail="database not reachable")
    return {"status": "READY"}
