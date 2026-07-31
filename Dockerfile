# syntax=docker/dockerfile:1.7
# ── Stage 1: Build React frontend ─────────────────────────────────────────
FROM node:20-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci --only=production
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Build Python wheels ──────────────────────────────────────────
FROM python:3.12-slim AS builder
WORKDIR /build
RUN pip install --upgrade pip wheel
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ── Stage 3: Runtime ──────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/*.whl \
    && rm -rf /wheels

COPY app/ ./app/
COPY templates/ ./templates/
COPY dns_engine/ ./dns_engine/

# Copy built React frontend from Stage 1
COPY --from=frontend-builder /frontend/dist ./frontend/dist

USER appuser

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT --no-access-log"]
