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

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project
COPY . .

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

# Run entrypoint (migrations + server)
ENTRYPOINT ["/app/entrypoint.sh"]
