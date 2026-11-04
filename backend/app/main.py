"""
SmartPulse Backend Application Entrypoint
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .model_loader import load_all_artifacts
from .routers import (
    overview,
    predict,
    whatif,
    explain,
    stats,
    performance,
    report
)
from . import config

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load models and artifacts into memory once
    load_all_artifacts()
    yield
    # Shutdown logic if any

app = FastAPI(
    title="SmartPulse API",
    description="Student Stress & Burnout Monitoring Platform API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(overview.router)
app.include_router(predict.router)
app.include_router(whatif.router)
app.include_router(explain.router)
app.include_router(stats.router)
app.include_router(performance.router)
app.include_router(report.router)

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "SmartPulse API",
        "tagline": "Understand stress. Predict burnout. Take action."
    }
