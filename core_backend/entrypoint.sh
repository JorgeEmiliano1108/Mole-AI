#!/bin/bash
set -e

echo "========================================="
echo " Mole AI — Django Backend Entrypoint     "
echo "========================================="

# Validate critical environment variables for Cloud-Native Production
if [ "${DEBUG}" != "True" ] && [ "${DEBUG}" != "true" ]; then
  echo "[0/4] Validating required Cloud-Native env vars..."
  missing=0
  # Strict variables for AWS/NVIDIA migration
  for v in SECRET_KEY POSTGRES_PASSWORD POSTGRES_HOST AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY NVIDIA_API_KEY; do
    if [ -z "${!v}" ]; then
      echo "  ERROR: required env var '${v}' is not set"
      missing=1
    fi
  done
  if [ "$missing" -eq 1 ]; then
    echo "Infrastructure variables missing; aborting startup." >&2
    exit 1
  fi
fi

# Wait for the RDS/PostgreSQL database to be ready
DB_HOST=${POSTGRES_HOST:-mole-ai-db}
DB_PORT=${POSTGRES_PORT:-5432}
DB_MAX_RETRIES=${DB_MAX_RETRIES:-30}
DB_RETRY_COUNT=0

echo "[1/4] Waiting for database at ${DB_HOST}:${DB_PORT} (max ${DB_MAX_RETRIES} retries)..."
while ! python -c "
import socket, sys, os
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(2)
try:
    s.connect(('${DB_HOST}', int('${DB_PORT}')))
    s.close()
except Exception:
    sys.exit(1)
" 2>/dev/null; do
  DB_RETRY_COUNT=$((DB_RETRY_COUNT + 1))
  if [ "$DB_RETRY_COUNT" -ge "$DB_MAX_RETRIES" ]; then
    echo "  CRITICAL: Database at ${DB_HOST}:${DB_PORT} unreachable after ${DB_MAX_RETRIES} attempts. Aborting." >&2
    exit 1
  fi
  echo "  DB not ready (RDS/Postgres) — retrying in 2s... (${DB_RETRY_COUNT}/${DB_MAX_RETRIES})"
  sleep 2
done
echo "  DB connection established."

# Apply migrations
echo "[2/4] Applying database migrations..."
python manage.py migrate --noinput

# Set up Superuser
echo "[3/4] Setting up Superuser..."
if [ -f "setup_superuser.py" ]; then
  # Se ejecuta el script. Si falla (ej. el usuario ya existe), el '|| true' evita que el contenedor muera.
  python setup_superuser.py || echo "  Notice: Superuser might already exist or script returned non-zero."
else
  echo "  Notice: setup_superuser.py not found in root directory. Skipping."
fi

# Collect static files (S3 Trap Protection)
echo "[4/4] Collecting static files..."
if [ "${SKIP_COLLECTSTATIC}" = "True" ] || [ "${SKIP_COLLECTSTATIC}" = "true" ]; then
  echo "  Notice: SKIP_COLLECTSTATIC is True. Skipping S3 upload to speed up boot time."
else
  python manage.py collectstatic --noinput
  echo "  Static files uploaded successfully."
fi

if [ "$#" -gt 0 ]; then
  echo "========================================="
  echo " Executing custom command: $@"
  echo "========================================="
  exec "$@"
else
  echo "========================================="
  echo " Starting Daphne on 0.0.0.0:8000"
  echo "========================================="
  exec daphne -b 0.0.0.0 -p 8000 mole_ai_backend.asgi:application
fi