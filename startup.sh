#!/bin/bash
# Startup script for Azure App Service (Python)

echo "Starting Azure DNS Portal..."

# Install dependencies
pip install -r requirements.txt --no-cache-dir

# Start FastAPI with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000
