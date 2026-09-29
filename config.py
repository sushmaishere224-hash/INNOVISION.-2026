"""Load shared project .env (repo root) once for the backend."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = Path(__file__).resolve().parent.parent

# Prefer monorepo root .env; fall back to backend/.env for local overrides.
load_dotenv(ROOT_DIR / ".env")
load_dotenv(BACKEND_DIR / ".env", override=False)


def get_env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip()


def get_cors_origins() -> list[str]:
    raw = get_env("CORS_ORIGINS", "")
    origins = [part.strip() for part in (raw or "").split(",") if part.strip()]
    frontend = get_env("FRONTEND_URL")
    if frontend and frontend not in origins:
        origins.append(frontend)
    if not origins:
        origins = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    return origins
