# Setup Guide - Health Check Panel

## Quick Setup (Recommended)

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose

### One-Command Setup

```bash
make setup
```

This command will:
1. Install backend dependencies (Python virtual environment)
2. Install frontend dependencies (Node.js packages)
3. Start PostgreSQL database via Docker
4. Run database migrations
5. Create default admin user

### Start All Services

```bash
# Run in background
make up-bg

# OR run interactively (shows frontend logs)
make up-interactive
```

### Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs

### Default Login Credentials

```
Email: admin@admin.com
Password: admin
```

## Manual Setup (Step by Step)

### 1. Install Dependencies

```bash
# Install both backend and frontend
make install

# OR install separately
make install-backend   # Python dependencies
make install-frontend  # Node.js dependencies
```

### 2. Start Database

```bash
make db-up
```

This starts PostgreSQL 16 in Docker with:
- Database: `healthcheck`
- User: `healthcheck`
- Password: `dev123`
- Port: `5432`

### 3. Run Database Migrations

```bash
make migrate
```

### 4. Seed Default Admin User

```bash
make seed
```

Creates admin user:
- Email: `admin@admin.com`
- Password: `admin`
- Role: `admin`

### 5. Start Services

```bash
# Option 1: All services in background
make up-bg

# Option 2: Interactive mode (shows logs)
make up-interactive

# Option 3: Individual services
make backend    # Terminal 1
make frontend   # Terminal 2
```

## Available Make Commands

### Setup & Installation
```bash
make help              # Show all available commands
make setup             # Complete first-time setup
make install           # Install all dependencies
make install-backend   # Install Python dependencies
make install-frontend  # Install Node.js dependencies
```

### Running Services
```bash
make up-bg             # Start all services in background
make up-interactive    # Start with interactive logs
make backend           # Start only backend (interactive)
make frontend          # Start only frontend (interactive)
make down              # Stop all services
```

### Database Management
```bash
make db-up             # Start PostgreSQL
make db-down           # Stop PostgreSQL
make migrate           # Run migrations
make migrate-create    # Create new migration (MSG="description")
make seed              # Create default admin user
make db-reset          # Reset database (WARNING: deletes all data)
```

### Development
```bash
make status            # Check status of all services
make logs              # Show logs from all services
make test              # Run API tests
make test-backend      # Test backend health
make test-frontend     # Test frontend
make clean             # Clean all generated files
```

## Testing the Installation

### 1. Check Services Status

```bash
make status
```

Should show all services as "Running".

### 2. Test Backend API

```bash
# Health check
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","app":"Health Check Panel","environment":"development"}
```

### 3. Test Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@admin.com&password=admin"

# Should return access_token and refresh_token
```

### 4. Test Frontend

Open http://localhost:3000 in browser and login with:
- Email: `admin@admin.com`
- Password: `admin`

## Quick API Tutorial

### 1. Login and Get Token

```bash
# Login
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@admin.com&password=admin")

# Extract token (requires jq)
TOKEN=$(echo $RESPONSE | jq -r '.access_token')
echo "Token: $TOKEN"
```

### 2. Create a Site

```bash
curl -X POST http://localhost:8000/api/v1/sites \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Google",
    "url": "https://google.com",
    "description": "Search engine"
  }'
```

### 3. List Available Check Types

```bash
curl http://localhost:8000/api/v1/checks/types \
  -H "Authorization: Bearer $TOKEN"
```

Should return:
- `http` - HTTP status checks
- `dns` - DNS record checks

### 4. Create an HTTP Check

```bash
curl -X POST http://localhost:8000/api/v1/checks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "site_id": 1,
    "check_type": "http",
    "name": "Homepage Status Check",
    "interval_seconds": 60,
    "configuration": {
      "expected_status_code": 200,
      "timeout_seconds": 10,
      "follow_redirects": true,
      "verify_ssl": true,
      "max_response_time_ms": 3000
    }
  }'
```

### 5. View Check Results

```bash
# Wait ~60 seconds for first check to execute
sleep 60

# Get results
curl http://localhost:8000/api/v1/checks/1/results \
  -H "Authorization: Bearer $TOKEN"
```

### 6. Test Real-time Updates (SSE)

```bash
# Open SSE stream (stays connected)
curl -N http://localhost:8000/api/v1/stream/updates \
  -H "Authorization: Bearer $TOKEN"

# In another terminal, trigger a check:
curl -X POST http://localhost:8000/api/v1/checks/1/run-now \
  -H "Authorization: Bearer $TOKEN"

# You should see the update in the SSE stream
```

## Environment Configuration

### Backend Environment Variables

Create or edit `backend/.env`:

```env
# Application
SECRET_KEY=dev-secret-key-change-in-production
ENVIRONMENT=development
CORS_ORIGINS=["http://localhost:3000"]

# Database (default for Docker Compose)
DATABASE_URL=postgresql+asyncpg://healthcheck:dev123@localhost:5432/healthcheck

# JWT
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ALGORITHM=HS256

# SMTP (optional, for email notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@healthcheck.com
```

### Frontend Configuration

Frontend is configured via `frontend/astro.config.mjs`.

API endpoint is proxied automatically:
- Development: `http://localhost:8000` (via Vite proxy)
- Production: Same origin (served by FastAPI)

## Database Migrations

### Create New Migration

```bash
# Using Makefile
make migrate-create MSG="add new table"

# OR manually
cd backend
source venv/bin/activate
alembic revision --autogenerate -m "add new table"
```

### Apply Migrations

```bash
make migrate
```

### Rollback Migration

```bash
cd backend
source venv/bin/activate
alembic downgrade -1
```

### View Migration History

```bash
cd backend
source venv/bin/activate
alembic history
alembic current
```

## Troubleshooting

### Services Not Starting

**Check status:**
```bash
make status
```

**View logs:**
```bash
# All services
make logs

# Backend only
tail -f /tmp/healthcheck-backend.log

# Frontend only
tail -f /tmp/healthcheck-frontend.log

# Database only
docker-compose logs postgres
```

### Database Connection Error

**Check PostgreSQL is running:**
```bash
docker-compose ps
```

**Restart database:**
```bash
make db-down
make db-up
```

**Test connection manually:**
```bash
psql -h localhost -U healthcheck -d healthcheck
# Password: dev123
```

### Migration Errors

**Check database state:**
```bash
cd backend
source venv/bin/activate
alembic current
```

**Reset database (WARNING: deletes all data):**
```bash
make db-reset
```

### Frontend Build Errors

**Clean and reinstall:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Check Node.js version:**
```bash
node --version  # Should be 20+
```

### Port Already in Use

**Check what's using the port:**
```bash
# macOS/Linux
lsof -i :3000
lsof -i :8000
lsof -i :5432
```

**Kill process on port:**
```bash
# macOS/Linux
lsof -ti:3000 | xargs kill -9
lsof -ti:8000 | xargs kill -9

# OR use make down
make down
```

### APScheduler Not Starting

**Check backend logs:**
```bash
tail -f /tmp/healthcheck-backend.log | grep -i "scheduler"
```

Should see:
```
✅ APScheduler started
✅ Synced X check schedules
```

**Check jobs in database:**
```bash
psql -h localhost -U healthcheck -d healthcheck -c "SELECT * FROM apscheduler_jobs;"
```

### Login Not Working

**Check seeder ran successfully:**
```bash
cd backend
source venv/bin/activate
PYTHONPATH=. python app/seed.py
```

**Verify user exists:**
```bash
psql -h localhost -U healthcheck -d healthcheck -c "SELECT email, role FROM users;"
```

Should show:
```
       email        | role
--------------------+-------
 admin@admin.com    | admin
```

### Real-time Updates Not Working

**Check SSE endpoint:**
```bash
curl -N http://localhost:8000/api/v1/stream/updates \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Check CORS configuration:**
- Verify `CORS_ORIGINS` in `backend/.env` includes frontend URL
- Check browser console for CORS errors

**Check event bus:**
- SSE uses in-memory event bus
- Events only work within single backend instance
- For multiple instances, migrate to PostgreSQL LISTEN/NOTIFY

## Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for DigitalOcean Apps deployment guide.

### Quick Production Checklist

- [ ] Change `SECRET_KEY` to random secure value
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure `CORS_ORIGINS` with production URL
- [ ] Setup external PostgreSQL database
- [ ] Configure SMTP settings for notifications
- [ ] Enable HTTPS
- [ ] Setup monitoring and alerts

## Additional Resources

- **API Documentation**: http://localhost:8000/api/docs (interactive Swagger UI)
- **Makefile Guide**: [MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md)
- **Frontend Docs**: [frontend/README.md](frontend/README.md)
- **Deployment Guide**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Main README**: [README.md](README.md)

## Support

For issues and questions:
- Check logs: `make logs`
- Check status: `make status`
- View API docs: http://localhost:8000/api/docs
- GitHub Issues: [Create an issue](https://github.com/your-username/health-check-panel/issues)
