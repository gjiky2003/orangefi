# ═══════════════════════════════════════════════════════════════════════════════
# OrangeFi Backend — Multi-stage Dockerfile
# ═══════════════════════════════════════════════════════════════════════════════
#
# Stage 1: Builder — Install dependencies
# Stage 2: Runtime — Minimal image with compiled deps only
#
# Build:  docker build -t orangefi-backend .
# Run:    docker run -p 8000:8000 orangefi-backend
#
# ═══════════════════════════════════════════════════════════════════════════════

# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

# Install build dependencies required by some Python packages (psycopg2, numpy, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only requirements first for layer caching
COPY requirements.txt .

# Install dependencies into a local user directory (shallow copy pattern)
RUN pip install --user --no-cache-dir --upgrade pip && \
    pip install --user --no-cache-dir -r requirements.txt

# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim

# Runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /root/.local /root/.local

# Ensure local bin is in PATH
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Create non-root user for security
RUN groupadd -r orangefi && useradd -r -g orangefi -d /app -s /sbin/nologin orangefi && \
    chown -R orangefi:orangefi /app

USER orangefi

# ── Expose & Healthcheck ──
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

# ── Default Command ──
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
