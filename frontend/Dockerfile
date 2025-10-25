# Optimized multi-stage Dockerfile for Next.js frontend application (balanced)

# ---------------------
# Builder stage
# ---------------------
FROM node:22-slim AS builder

# Add custom CA certificate and trust for build-time network access
COPY docker/certs/nscacert.pem /usr/local/share/ca-certificates/nscacert.crt
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates wget curl && \
    update-ca-certificates && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Ensure Node and system tools use the updated CA bundle
ENV NODE_EXTRA_CA_CERTS=/usr/local/share/ca-certificates/nscacert.crt \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    NEXT_TELEMETRY_DISABLED=1

WORKDIR /app

# Install dependencies with cache-friendly layers
COPY package*.json ./
RUN npm ci

# Copy source and build
RUN mkdir -p /app/public
COPY . .
RUN npm run build

# ---------------------
# Development runtime stage
# ---------------------
FROM node:22-slim AS dev

COPY docker/certs/nscacert.pem /usr/local/share/ca-certificates/nscacert.crt
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates wget curl && \
    update-ca-certificates && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV NODE_EXTRA_CA_CERTS=/usr/local/share/ca-certificates/nscacert.crt \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

WORKDIR /app

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 --ingroup nodejs --home /home/nextjs --shell /bin/bash nextjs && \
    mkdir -p /home/nextjs && \
    chown -R nextjs:nodejs /home/nextjs

ENV HOME=/home/nextjs \
    NPM_CONFIG_CACHE=/home/nextjs/.npm

COPY --chown=nextjs:nodejs --from=builder /app /app

USER nextjs

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0", "--port", "3000"]

# ---------------------
# Runtime stage
# ---------------------
FROM node:22-slim AS runner

# Add CA cert and minimal tools (wget is required by docker-compose healthcheck)
COPY docker/certs/nscacert.pem /usr/local/share/ca-certificates/nscacert.crt
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates wget curl && \
    update-ca-certificates && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Environment
ENV NODE_EXTRA_CA_CERTS=/usr/local/share/ca-certificates/nscacert.crt \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

WORKDIR /app

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 --ingroup nodejs --home /home/nextjs --shell /bin/bash nextjs && \
    mkdir -p /home/nextjs && \
    chown -R nextjs:nodejs /home/nextjs

ENV HOME=/home/nextjs \
    NPM_CONFIG_CACHE=/home/nextjs/.npm

# Install only production dependencies (ensure cache dir owned afterward)
COPY --chown=nextjs:nodejs package*.json ./
RUN mkdir -p /home/nextjs/.npm && \
    npm ci --omit=dev && \
    npm cache clean --force && \
    chown -R nextjs:nodejs /home/nextjs/.npm /app

# Copy build artifacts and needed assets from builder
COPY --chown=nextjs:nodejs --from=builder /app/.next /app/.next
COPY --chown=nextjs:nodejs --from=builder /app/public /app/public

# Switch to non-root
USER nextjs

# Expose port
EXPOSE 3000

# Health check using Node.js built-in http module
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000/api/health', (res) => { process.exit(res.statusCode === 200 ? 0 : 1) }).on('error', () => process.exit(1))" || exit 1

# Start command (will be overridden by docker-compose for development)
CMD ["npm", "start"]