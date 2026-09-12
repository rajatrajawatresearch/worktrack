#!/bin/sh
set -e

echo "[entrypoint] Applying database migrations..."
alembic upgrade head

if [ "${SEED_SUPERADMIN:-0}" = "1" ]; then
  echo "[entrypoint] Seeding initial data..."
  if [ "${SEED_DEMO:-0}" = "1" ]; then
    python -m app.seed --demo || true
  else
    python -m app.seed || true
  fi
fi

echo "[entrypoint] Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers "${WEB_CONCURRENCY:-1}"
