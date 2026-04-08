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

import os
import shutil

from fastapi import FastAPI, File, UploadFile, Header, HTTPException
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


# ── Temporary DB upload endpoint ─────────────────────────────────────────────
# Protected by ADMIN_TOKEN env var. Remove after initial data seed.

ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
DB_PATH = _PROJECT_ROOT / "data" / "landos.db"


@app.post("/admin/upload-db")
async def upload_db(
    file: UploadFile = File(...),
    authorization: str = Header(...),
):
    if not ADMIN_TOKEN or authorization != f"Bearer {ADMIN_TOKEN}":
        raise HTTPException(status_code=403, detail="Forbidden")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DB_PATH, "wb") as f:
        shutil.copyfileobj(file.file, f)
    size_mb = DB_PATH.stat().st_size / (1024 * 1024)
    return {"status": "ok", "size_mb": round(size_mb, 1), "path": str(DB_PATH)}
