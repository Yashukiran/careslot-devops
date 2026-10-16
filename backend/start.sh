#!/bin/sh
set -e

echo "running database migrations..."
alembic upgrade head

if [ "${SEED_DATA:-false}" = "true" ]; then
    python -m app.seed
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers "${WORKERS:-2}" --proxy-headers
