FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install minimal system deps required for Python packages and image processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    libjpeg-dev \
    zlib1g-dev \
    libgomp1 \
    libstdc++6 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copy requirements and install
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel && \
    python -m pip install --no-cache-dir -r /app/requirements.txt

# Copy service code
COPY . /app/ms1_vision

# Ensure non-root user owns the code
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8001

# Run uvicorn with a single worker (adjust workers in production as needed)
CMD ["uvicorn", "ms1_vision.app.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]
