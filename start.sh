#!/bin/bash
# Simple script to start backend and frontend in background

set -e

echo "🚀 Starting Health Check Panel..."
echo ""

# Start database
echo "📦 Starting PostgreSQL..."
docker-compose up -d postgres
sleep 3
echo "✓ PostgreSQL started"
echo ""

# Start backend in background
echo "🔧 Starting backend..."
cd backend
source venv/bin/activate
nohup uvicorn app.main:app --reload --port 8000 > /tmp/healthcheck-backend.log 2>&1 &
BACKEND_PID=$!
cd ..
echo "✓ Backend started (PID: $BACKEND_PID)"
echo "  Logs: tail -f /tmp/healthcheck-backend.log"
sleep 2
echo ""

# Start frontend in background
echo "🎨 Starting frontend..."
cd frontend
nohup npm run dev > /tmp/healthcheck-frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "✓ Frontend started (PID: $FRONTEND_PID)"
echo "  Logs: tail -f /tmp/healthcheck-frontend.log"
echo ""

# Wait a bit for services to start
echo "⏳ Waiting for services to initialize..."
sleep 5
echo ""

# Check services
echo "✅ Services started!"
echo ""
echo "URLs:"
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/api/docs"
echo ""
echo "PIDs saved to:"
echo "  echo $BACKEND_PID > /tmp/healthcheck-backend.pid"
echo "  echo $FRONTEND_PID > /tmp/healthcheck-frontend.pid"
echo $BACKEND_PID > /tmp/healthcheck-backend.pid
echo $FRONTEND_PID > /tmp/healthcheck-frontend.pid
echo ""
echo "To stop:"
echo "  make down"
echo "  or: kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "View logs:"
echo "  tail -f /tmp/healthcheck-backend.log"
echo "  tail -f /tmp/healthcheck-frontend.log"
