# ==============================================================================
# frontend/Dockerfile — Multi-Stage Build
# ==============================================================================

# ── Stage 1: Builder ───────────────────────────────────────────────────────────
FROM node:22-alpine AS builder

# Activate pnpm via Corepack (SEC-01 / SEC-03)
RUN corepack enable && corepack prepare pnpm@11.1.3 --activate

WORKDIR /app

# Copy lockfile and package manifest first (layer cache optimization)
COPY package.json pnpm-lock.yaml .npmrc ./
COPY vite.config.js ./
COPY tailwind.config.js ./
COPY postcss.config.js ./
COPY src/ ./src/
COPY public/ ./public/
COPY *.html ./

# Supply Chain Hardening: frozen lockfile + blocked scripts + esbuild whitelist
RUN pnpm install --frozen-lockfile --ignore-scripts && \
    pnpm rebuild esbuild && \
    pnpm run build

# ── Stage 2: Runtime (Nginx mínimo) ───────────────────────────────────────────
FROM nginx:1.25-alpine AS runtime

# Hardening: no correr como root
RUN sed -i 's/^user  nginx;/user nginx;/' /etc/nginx/nginx.conf || true

# Copiar estáticos compilados desde el builder
COPY --from=builder /app/dist/ /usr/share/nginx/html/

# Copiar configuración del API Gateway (desde el contexto frontend/)
COPY nginx.conf /etc/nginx/nginx.conf
COPY cors_headers.conf /etc/nginx/conf.d/cors_headers.conf

# Hardening: usuario no root
USER nginx

EXPOSE 80

# Healthcheck — verify nginx responds
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

# Hardening: rootfs read-only, logs a /tmp (se sobreescribe con tmpfs en orquestación)
CMD ["nginx", "-g", "daemon off;"]
