# syntax=docker/dockerfile:1.7
# Multi-stage Dockerfile for the Vite React SPA frontend.

ARG NODE_VERSION=22-slim
ARG NGINX_VERSION=1.30.3-alpine

# ---------------------
# Base: certs and tooling
# ---------------------
FROM node:${NODE_VERSION} AS base

COPY docker/certs/nscacert.pem /usr/local/share/ca-certificates/nscacert.crt
RUN apt-get update && \
  apt-get install -y --no-install-recommends ca-certificates curl && \
  update-ca-certificates && \
  apt-get clean && rm -rf /var/lib/apt/lists/*

ENV NODE_EXTRA_CA_CERTS=/usr/local/share/ca-certificates/nscacert.crt \
  SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

WORKDIR /app

# ---------------------
# Dependencies
# ---------------------
FROM base AS deps
COPY package*.json ./
RUN npm ci

# ---------------------
# Build
# ---------------------
FROM deps AS builder
ARG FRONTEND_ENV_FILE=.env.docker
COPY . .
RUN if [ -n "${FRONTEND_ENV_FILE}" ] && [ -f "${FRONTEND_ENV_FILE}" ] && [ "${FRONTEND_ENV_FILE}" != ".env.production" ] && [ "${FRONTEND_ENV_FILE}" != "./.env.production" ]; then \
    cp "${FRONTEND_ENV_FILE}" .env.production; \
  fi
RUN npm run build

# ---------------------
# Development
# ---------------------
FROM deps AS dev
ENV NODE_ENV=development
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]

# ---------------------
# Runtime: static SPA server
# ---------------------
FROM nginxinc/nginx-unprivileged:${NGINX_VERSION} AS runner

COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1:8080/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
