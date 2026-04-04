"""LandOS FastAPI server — serves pipeline intelligence to NEXUS frontend.

Usage:
    cd landos && uvicorn api.main:app --reload --port 8000

Or:
    python3 -m uvicorn api.main:app --reload --port 8000
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path for src.* imports
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.clusters import router as clusters_router
from api.routes.opportunities import router as opportunities_router
from api.routes.signals import router as signals_router
from api.routes.stats import router as stats_router
from api.routes.parcels import router as parcels_router
from api.routes.strategic import router as strategic_router

app = FastAPI(
    title="LandOS API",
    description="Land intelligence API powering BaseMod NEXUS",
    version="0.1.0",
)

# CORS — allow NEXUS frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",       # Vite dev server
        "http://localhost:4173",       # Vite preview
        "https://agents.basemodhomes.com",
        "https://landos-nexus.netlify.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(clusters_router, prefix="/api")
app.include_router(opportunities_router, prefix="/api")
app.include_router(signals_router, prefix="/api")
app.include_router(stats_router, prefix="/api")
app.include_router(parcels_router, prefix="/api")
app.include_router(strategic_router, prefix="/api")


@app.get("/")
def root():
    return {"status": "ok", "service": "LandOS API", "version": "0.1.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}
