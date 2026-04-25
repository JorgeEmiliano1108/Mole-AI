# ==============================================================================
# frontend/Dockerfile — Multi-Stage Build
# ==============================================================================

# ── Stage 1: Builder ───────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Copiar solo lo necesario para build
# IMPORTANTE: context es la raíz del repo (../), requiere prefijo frontend/
COPY frontend/package*.json ./
COPY frontend/vite.config.js ./
COPY frontend/tailwind.config.js ./
COPY frontend/postcss.config.js ./
COPY frontend/src/ ./src/
COPY frontend/static/ ./static/
COPY frontend/*.html ./

# Instalar dependencias y compilar
RUN npm ci
RUN npm run build

# ── Stage 2: Runtime (Nginx mínimo) ───────────────────────────────────────────
FROM nginx:1.25-alpine AS runtime

# Copiar estáticos compilados desde el builder
COPY --from=builder /app/dist/ /usr/share/nginx/html/

# Copiar configuración del API Gateway
COPY infrastructure/nginx/nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]