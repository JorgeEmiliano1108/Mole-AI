#!/usr/bin/env bash
set -o errexit

# Install dependencies
python -m pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate --no-input
