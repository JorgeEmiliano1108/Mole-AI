# ==============================================================================
# frontend/Dockerfile — Multi-Stage Build
# ==============================================================================

# ── Stage 1: Builder ───────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Copiar solo lo necesario para build
# Context es frontend/, no requiere prefijo
COPY package*.json ./
COPY vite.config.js ./
COPY tailwind.config.js ./
COPY postcss.config.js ./
COPY src/ ./src/
COPY static/ ./static/
COPY public/ ./public/
COPY *.html ./

# Supply Chain Hardening: bloquear scripts de terceros, permitir solo esbuild (Vite)
RUN npm ci --ignore-scripts && \
    npm rebuild esbuild && \
    npm run build

# ── Stage 2: Runtime (Nginx mínimo) ───────────────────────────────────────────
FROM nginx:1.25-alpine AS runtime

# Copiar estáticos compilados desde el builder
COPY --from=builder /app/dist/ /usr/share/nginx/html/

# Copiar carpeta static/ para apiService.js y otros assets estáticos
COPY --from=builder /app/static/ /usr/share/nginx/static/

# Copiar configuración del API Gateway (desde el contexto frontend/)

COPY nginx.conf /etc/nginx/nginx.conf
COPY cors_headers.conf /etc/nginx/conf.d/cors_headers.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
