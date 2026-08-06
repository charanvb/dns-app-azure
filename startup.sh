#!/bin/bash
# Startup script for Azure App Service (Python)

echo "Starting Azure DNS Portal..."

# Install dependencies
pip install -r requirements.txt --no-cache-dir

# Schema is the source of truth in Postgres; safe to re-run idempotently on every boot.
alembic upgrade head

# Local test users only outside production.
if [ "$ENVIRONMENT" != "production" ]; then
    python -m scripts.seed_users
fi

# Start FastAPI via Gunicorn + Uvicorn workers (production-grade, matches App Service sizing)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind=0.0.0.0:8000
