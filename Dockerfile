# Multi-stage build for Health Check Panel
# Stage 1: Build Next.js frontend (placeholder - will be implemented later)
# Stage 2: Python backend with FastAPI

FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# TODO: Copy built frontend from stage 1 when frontend is ready
# COPY --from=frontend-builder /app/frontend/out ./frontend/dist

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run database migrations and start application
CMD alembic -c backend/alembic.ini upgrade head && \
    uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
