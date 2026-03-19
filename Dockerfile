FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies including those for pgvector/postgres
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user (M3: hardening)
RUN useradd --create-home --shell /bin/bash appuser

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project
COPY . .

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Ensure non-root user owns the code
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Run entrypoint (migrations + server)
ENTRYPOINT ["/app/entrypoint.sh"]
