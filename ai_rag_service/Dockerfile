FROM python:3.11-slim

LABEL maintainer="Mole AI Team"
LABEL service="ai_rag_service"
LABEL description="RAG Service - Phi-3.5 Reasoning"
LABEL architecture="hexagonal"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    API_HOST=0.0.0.0 \
    API_PORT=8002 \
    LOG_LEVEL=INFO

WORKDIR /app


# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .


# Install torch CPU-only and Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Create storage dir
RUN mkdir -p storage/vectors

# Create non-root user
RUN useradd -m -u 1000 aiservice && \
    chown -R aiservice:aiservice /app

USER aiservice

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=720s --retries=3 \
    CMD curl -f http://localhost:8002/rag/health || exit 1

EXPOSE 8002

# Run FastAPI
CMD ["python", "-m", "uvicorn", "ai_rag_service.main:app", \
     "--host", "0.0.0.0", "--port", "8002", "--log-level", "info"]
