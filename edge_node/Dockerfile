# ==========================================
# Etapa 1: Builder
# ==========================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Instala dependencias del sistema necesarias para compilar paquetes
RUN apt-get update && apt-get install -y --no-install-recommends build-essential

COPY requirements.txt .

# Compila las dependencias en "wheels" (archivos binarios empaquetados)
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# ==========================================
# Etapa 2: Runner (Imagen Final)
# ==========================================
FROM python:3.11-slim AS runner

WORKDIR /app

# Copia solo los wheels compilados de la etapa anterior
COPY --from=builder /build/wheels /wheels
COPY --from=builder /build/requirements.txt .

# Instala los wheels sin usar la red para descargar de nuevo
RUN pip install --no-cache /wheels/* && rm -rf /wheels

# Copia el código fuente
COPY . .

# Crea el script de inicio para correr ambos demonios
RUN echo '#!/bin/bash\npython store_forward_daemon.py &\npython openclaw_gateway.py\nwait -n' > start.sh
RUN chmod +x start.sh

# Expone el puerto WebSocket para el ESP32
EXPOSE 18789

# Comando de arranque
CMD ["./start.sh"]