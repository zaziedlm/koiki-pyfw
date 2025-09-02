# Optimized Dockerfile for Next.js frontend application
FROM node:20-alpine

# Install libc6-compat for compatibility with Alpine and wget for health checks
RUN apk add --no-cache libc6-compat wget curl

# Set working directory
WORKDIR /app

# Create non-root user for security
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy package files and install dependencies
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

# Build for production (always build, then run dev or start based on environment)
RUN npm run build

# Create .next directory with proper permissions
RUN mkdir -p /app/.next && chown -R nextjs:nodejs /app

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Set environment variables
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
ENV NEXT_TELEMETRY_DISABLED=1

# Health check using Node.js built-in http module
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/api/health', (res) => { process.exit(res.statusCode === 200 ? 0 : 1) }).on('error', () => process.exit(1))" || exit 1

# Start command (will be overridden by docker-compose for development)
CMD ["npm", "start"]