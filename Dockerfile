# Multi-stage build for Health Check Panel
# Stage 1: Build Astro frontend
# Stage 2: Python backend with FastAPI

# ========== Stage 1: Frontend Build ==========
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Install dependencies
COPY frontend/package*.json ./
RUN npm ci

# Copy frontend source
COPY frontend/ ./

# Build the frontend (Astro static build)
RUN npm run build

# ========== Stage 2: Python Backend ==========
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s \
  CMD curl -f http://localhost:8000/health || exit 1

# Run database migrations and start application
CMD alembic -c backend/alembic.ini upgrade head && \
    uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
