"""Generate and validate Docker assets for the agent platform."""
from __future__ import annotations
from pathlib import Path
from typing import Any

DOCKERFILE = """# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
"""

COMPOSE = """services:
  api:
    build: .
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql://app:app@db:5432/app
      - REDIS_URL=redis://redis:6379/0
    depends_on: [db, redis]
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
      POSTGRES_DB: app
  redis:
    image: redis:7-alpine
"""

def write_assets(directory: str | Path) -> dict[str, Any]:
    d = Path(directory); d.mkdir(parents=True, exist_ok=True)
    (d/"Dockerfile").write_text(DOCKERFILE)
    (d/"docker-compose.yml").write_text(COMPOSE)
    (d/"requirements.txt").write_text("fastapi\nuvicorn\n")
    return validate_assets(d)

def validate_assets(directory: str | Path) -> dict[str, Any]:
    d = Path(directory)
    df = (d/"Dockerfile").read_text() if (d/"Dockerfile").exists() else ""
    checks = {
        "dockerfile_exists": bool(df),
        "multi_stage_or_slim": "slim" in df or "AS " in df,
        "no_latest_python_implicit": "python:" in df,
        "compose_exists": (d/"docker-compose.yml").exists(),
        "non_root_recommended": "USER " in df,  # optional
    }
    return {"ok": checks["dockerfile_exists"] and checks["compose_exists"], "checks": checks, "path": str(d)}
