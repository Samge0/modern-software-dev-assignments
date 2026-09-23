import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .db import apply_seed_if_needed, engine
from .models import Base
from .routers import action_items as action_items_router
from .routers import notes as notes_router

app = FastAPI(title="Modern Software Dev Starter (Week 7)", version="0.1.0")

# Ensure data dir exists
Path("data").mkdir(parents=True, exist_ok=True)

# Mount static frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")


# FIX (semgrep: wildcard-cors): replaced allow_origins=["*"] with an explicit
# origin allowlist from env. "*" combined with allow_credentials=True is
# rejected by browsers anyway and signals a permissive policy (CWE-942).
_origins = os.environ.get("CORS_ALLOW_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Compatibility with FastAPI lifespan events; keep on_event for simplicity here
@app.on_event("startup")
def startup_event() -> None:
    Base.metadata.create_all(bind=engine)
    apply_seed_if_needed()


@app.get("/")
async def root() -> FileResponse:
    return FileResponse("frontend/index.html")


# Routers
app.include_router(notes_router.router)
app.include_router(action_items_router.router)
