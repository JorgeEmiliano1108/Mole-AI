#!/bin/bash
set -e

echo "========================================="
echo " Mole AI — Django Backend Entrypoint"
echo "========================================="

# Validate critical environment variables in non-debug mode
if [ "${DEBUG}" != "True" ] && [ "${DEBUG}" != "true" ]; then
  echo "[0/3] Validating required environment variables for non-debug startup..."
  missing=0
  for v in SECRET_KEY SUPABASE_DB_PASSWORD POSTGRES_PASSWORD MINIO_ROOT_PASSWORD; do
    if [ -z "${!v}" ]; then
      echo "  ERROR: required env var '${v}' is not set"
      missing=1
    fi
  done
  if [ "$missing" -eq 1 ]; then
    echo "One or more required environment variables are missing; aborting startup." >&2
    exit 1
  fi
fi

# Wait for the database to be ready
echo "[1/3] Waiting for database at ${SUPABASE_DB_HOST}:${SUPABASE_DB_PORT}..."
while ! python -c "
import socket, sys, os
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.connect((os.environ.get('SUPABASE_DB_HOST','db'), int(os.environ.get('SUPABASE_DB_PORT','5432'))))
    s.close()
except Exception:
    sys.exit(1)
" 2>/dev/null; do
  echo "  DB not ready yet — retrying in 2s..."
  sleep 2
done
echo "  DB is accepting connections."

# Apply migrations
echo "[2/3] Applying database migrations..."
python manage.py migrate --noinput

# Collect static files (silently)
echo "[3/3] Collecting static files..."
python manage.py collectstatic --noinput 2>/dev/null || true

echo "========================================="
echo " Starting Daphne on 0.0.0.0:8000"
echo "========================================="
exec daphne -b 0.0.0.0 -p 8000 mole_ai_backend.asgi:application
