# syntax=docker/dockerfile:1.7
# Multi-stage Dockerfile for the Vite React SPA frontend.

ARG NODE_VERSION=22.23.4-bookworm-slim
ARG NGINX_VERSION=1.30.3-trixie

# ---------------------
# Base: certs and tooling
# ---------------------
FROM node:${NODE_VERSION} AS base

# Optional organization CA; session proxy roots are supplied separately as BuildKit secrets.
RUN --mount=type=bind,source=docker/certs,target=/run/koiki-ca,readonly \
    if [ -f /run/koiki-ca/nscacert.pem ]; then \
      install -m 0644 /run/koiki-ca/nscacert.pem /usr/local/share/ca-certificates/nscacert.crt; \
    fi
RUN apt-get update && \
    apt-get upgrade -y && \
  apt-get install -y --no-install-recommends ca-certificates curl && \
  update-ca-certificates && \
  apt-get clean && rm -rf /var/lib/apt/lists/*

ENV NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt \
  SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

ARG NPM_VERSION=11.21.1
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/proxy_ca; fi; \
    npm install --global npm@${NPM_VERSION} --ignore-scripts --no-audit --strict-ssl=true

WORKDIR /app

# ---------------------
# Dependencies
# ---------------------
FROM base AS deps
COPY package*.json ./
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/proxy_ca; fi; \
    npm ci --strict-ssl=true

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

# Apply signed Debian security updates, then restore the upstream unprivileged UID.
USER root
RUN apt-get update && apt-get upgrade -y && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
USER 101

COPY --chmod=0644 docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder --chown=101:101 /app/dist /usr/share/nginx/html

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1:8080/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
