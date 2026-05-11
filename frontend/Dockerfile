# ═══════════════════════════════════════════════════════════════════════════════
# OrangeFi Frontend — Dockerfile
# ═══════════════════════════════════════════════════════════════════════════════
#
# Build:  docker build -t orangefi-frontend .
# Run:    docker run -p 3000:3000 orangefi-frontend
#
# ═══════════════════════════════════════════════════════════════════════════════

# ── Stage 1: Dependencies ─────────────────────────────────────────────────────
FROM node:20-alpine AS deps

WORKDIR /app

# Copy lock files first for layer caching
COPY package.json package-lock.json* ./

# Install production dependencies only
RUN npm ci --only=production

# ── Stage 2: Builder ──────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Copy lock files and install ALL dependencies (including devDeps)
COPY package.json package-lock.json* ./
RUN npm ci

# Copy source code
COPY tsconfig.json next.config.js postcss.config.js tailwind.config.ts ./
COPY src/ ./src/
COPY public/ ./public/ || true

# Build the Next.js application (output: standalone)
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# ── Stage 3: Runtime ──────────────────────────────────────────────────────────
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy standalone output from builder
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

# Set correct permissions
RUN chown -R nextjs:nodejs /app

USER nextjs

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/api/health || exit 1

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# ── Default Command (standalone output server) ──
CMD ["node", "server.js"]
