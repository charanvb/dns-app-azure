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

# Start FastAPI with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000
