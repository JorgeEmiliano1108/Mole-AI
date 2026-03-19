FROM python:3.11-slim

# Create non-root user
RUN groupadd -r app && useradd -r -g app -m -d /home/app app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# Install system deps needed for some Python packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       git \
       wget \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first for layer caching
COPY requirements.txt /app/requirements.txt

RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install --no-cache-dir -r /app/requirements.txt

# Copy application into proper module namespace
COPY . /app/ms2_rag_cag_service
RUN chown -R app:app /app

USER app

EXPOSE 8002

ENV PORT=8002
ENV PYTHONPATH=/app

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:8002", "ms2_rag_cag_service.app.main:app"]
