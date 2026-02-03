FROM python:3.11-slim

LABEL maintainer="Mole AI Team"
LABEL service="ai_vision_service"
LABEL description="Vision Service - Phi-3.5 Vision-Instruct Q4"
LABEL architecture="hexagonal"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    API_HOST=0.0.0.0 \
    API_PORT=8001 \
    LOG_LEVEL=INFO

WORKDIR /app

# Instala dependencias del sistema
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

# Copia requirements
COPY requirements.txt .

# Instala torch CPU-only y dependencias Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Crea usuario no-root
RUN useradd -m -u 1000 aiservice && \
    chown -R aiservice:aiservice /app

USER aiservice

# Health check real
HEALTHCHECK --interval=30s --timeout=30s --start-period=720s --retries=3 \
    CMD curl -f http://localhost:8001/vision/health || exit 1

EXPOSE 8001

# Comando de arranque (ajusta según tu app)
CMD ["python", "-m", "uvicorn", "ai_vision_service.main:app", "--host", "0.0.0.0", "--port", "8001", "--log-level", "info"]