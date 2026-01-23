# Makefile Commands Guide

## Quick Start

```bash
# Install all dependencies
make install

# Start everything (database + backend + frontend)
make up

# Stop everything
make down
```

## All Available Commands

### Main Commands

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make up` | Start everything (PostgreSQL + Backend + Frontend) |
| `make down` | Stop all services |
| `make dev` | Alias for `make up` |
| `make status` | Check status of all services |
| `make info` | Show project information and URLs |

### Installation

| Command | Description |
|---------|-------------|
| `make install` | Install all dependencies (backend + frontend) |
| `make install-backend` | Install only backend dependencies |
| `make install-frontend` | Install only frontend dependencies |

### Database

| Command | Description |
|---------|-------------|
| `make db-up` | Start only PostgreSQL |
| `make db-down` | Stop PostgreSQL |
| `make db-reset` | Reset database (deletes all data!) |
| `make migrate` | Run database migrations |
| `make migrate-create MSG="your message"` | Create new migration |
| `make shell-db` | Open PostgreSQL shell |
| `make logs-db` | Show PostgreSQL logs |

### Backend

| Command | Description |
|---------|-------------|
| `make backend` | Start only backend (http://localhost:8000) |
| `make test-backend` | Test backend health |
| `make shell-backend` | Open Python shell |
| `make prod-backend` | Run backend in production mode |

### Frontend

| Command | Description |
|---------|-------------|
| `make frontend` | Start only frontend (http://localhost:3000) |
| `make test-frontend` | Test frontend |
| `make build-frontend` | Build frontend for production |
| `make prod-frontend` | Run frontend in production mode |

### Testing

| Command | Description |
|---------|-------------|
| `make test` | Run complete API test suite |
| `make test-backend` | Test backend health |
| `make test-frontend` | Test frontend |

### Utilities

| Command | Description |
|---------|-------------|
| `make logs` | Show logs from all services |
| `make clean` | Clean all generated files |
| `make docker-build` | Build Docker image |
| `make docker-run` | Run Docker container |

## Usage Examples

### First Time Setup

```bash
# 1. Install dependencies
make install

# 2. Start database
make db-up

# 3. Run migrations
make migrate

# 4. Start everything
make up
```

### Daily Development

```bash
# Start development environment
make up

# In another terminal: check status
make status

# When done
make down
```

### Database Operations

```bash
# Reset database (careful!)
make db-reset

# Create new migration
make migrate-create MSG="add user table"

# Run migrations
make migrate

# Access database
make shell-db
```

### Run Services Individually

```bash
# Terminal 1: Database only
make db-up

# Terminal 2: Backend only
make backend

# Terminal 3: Frontend only
make frontend
```

### Testing

```bash
# Full API test suite
make test

# Check if services are running
make status

# Test backend health
make test-backend

# Test frontend
make test-frontend
```

### Production Build

```bash
# Build frontend for production
make build-frontend

# Build Docker image
make docker-build

# Run production backend
make prod-backend
```

### Logs and Debugging

```bash
# All service logs
make logs

# PostgreSQL logs only
make logs-db

# Python shell
make shell-backend

# Database shell
make shell-db
```

### Cleanup

```bash
# Clean all generated files
make clean

# Reset database
make db-reset
```

## What `make up` Does

When you run `make up`, it:

1. ✅ Starts PostgreSQL in Docker
2. ✅ Waits for database to be ready (3 seconds)
3. ✅ Starts backend (FastAPI) on port 8000
4. ✅ Starts frontend (Next.js) on port 3000
5. ✅ Shows combined logs with prefixes:
   - `[BACKEND]` - FastAPI logs
   - `[FRONTEND]` - Next.js logs

Press `Ctrl+C` to stop everything cleanly.

## Service URLs

After `make up`, access:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs
- **Database**: localhost:5432 (user: healthcheck, pass: dev123)

## Tips

### Check What's Running

```bash
make status
```

Output example:
```
Service Status:

PostgreSQL:  Running
Backend:     Running
Frontend:    Running
```

### Quick Info

```bash
make info
```

Shows all URLs, database credentials, and quick commands.

### Parallel Logs

When running `make up`, you'll see combined logs:

```
[BACKEND] INFO:     Application startup complete.
[FRONTEND] ▲ Next.js 14.2.0
[BACKEND] INFO:     Uvicorn running on http://127.0.0.1:8000
[FRONTEND] - Local:        http://localhost:3000
```

### Database Connection

```bash
# Open psql shell
make shell-db

# Inside psql:
\dt                          # List tables
SELECT * FROM users;         # Query users
\q                           # Quit
```

### Create Migration

```bash
# After modifying models
make migrate-create MSG="add new field to site"

# Apply migration
make migrate
```

## Troubleshooting

### "Port already in use"

```bash
# Stop everything first
make down

# Check status
make status

# Try again
make up
```

### "Database connection failed"

```bash
# Reset database
make db-reset

# Or just restart it
make db-down
make db-up
```

### "Backend not starting"

```bash
# Reinstall dependencies
make install-backend

# Run migrations
make migrate

# Try again
make backend
```

### "Frontend not starting"

```bash
# Reinstall dependencies
make install-frontend

# Try again
make frontend
```

### Clean Everything

```bash
# Stop services
make down

# Clean files
make clean

# Reinstall
make install

# Start fresh
make up
```

## Advanced Usage

### Custom Database

Edit `docker-compose.yml` or set environment variables before running.

### Different Ports

Edit the Makefile's `backend` or `frontend` targets to change ports.

### Production Deployment

```bash
# Build everything
make build-frontend
make docker-build

# Run in production mode
make prod-backend  # Terminal 1
make prod-frontend # Terminal 2
```

## Summary

**Most Common Commands:**

```bash
make install    # First time only
make up         # Start development
make down       # Stop everything
make status     # Check what's running
make test       # Run tests
make help       # See all commands
```

That's it! 🚀
