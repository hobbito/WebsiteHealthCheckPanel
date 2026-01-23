.PHONY: help up down install install-backend install-frontend backend frontend test clean logs status

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "$(BLUE)Health Check Panel - Available Commands$(NC)"
	@echo "========================================"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

up: ## Start everything (database + backend + frontend)
	@echo "$(BLUE)🚀 Starting Health Check Panel...$(NC)"
	@echo ""
	@$(MAKE) -s db-up
	@sleep 3
	@echo ""
	@echo "$(BLUE)Starting backend and frontend...$(NC)"
	@echo "$(YELLOW)Backend: http://localhost:8000$(NC)"
	@echo "$(YELLOW)Frontend: http://localhost:3000$(NC)"
	@echo "$(YELLOW)API Docs: http://localhost:8000/api/docs$(NC)"
	@echo ""
	@echo "$(GREEN)Opening two terminals is recommended:$(NC)"
	@echo "  Terminal 1: make backend"
	@echo "  Terminal 2: make frontend"
	@echo ""
	@echo "$(YELLOW)Or use 'make up-bg' to run in background$(NC)"
	@echo ""
	@$(MAKE) -j2 backend-bg frontend-bg

backend-bg: ## Run backend in background
	@cd backend && . venv/bin/activate && uvicorn app.main:app --reload --port 8000 > /tmp/healthcheck-backend.log 2>&1 &
	@echo "$(GREEN)✓ Backend started in background (logs: /tmp/healthcheck-backend.log)$(NC)"

frontend-bg: ## Run frontend in background
	@cd frontend && npm run dev > /tmp/healthcheck-frontend.log 2>&1 &
	@echo "$(GREEN)✓ Frontend started in background (logs: /tmp/healthcheck-frontend.log)$(NC)"

up-bg: db-up backend-bg frontend-bg ## Start all services in background
	@sleep 2
	@echo ""
	@echo "$(GREEN)✅ All services started in background$(NC)"
	@echo ""
	@echo "$(BLUE)URLs:$(NC)"
	@echo "  Frontend:  http://localhost:3000"
	@echo "  Backend:   http://localhost:8000"
	@echo "  API Docs:  http://localhost:8000/api/docs"
	@echo ""
	@echo "$(BLUE)Logs:$(NC)"
	@echo "  Backend:   tail -f /tmp/healthcheck-backend.log"
	@echo "  Frontend:  tail -f /tmp/healthcheck-frontend.log"
	@echo ""
	@echo "$(YELLOW)Stop with: make down$(NC)"

up-interactive: ## Start with interactive logs (recommended)
	@echo "$(BLUE)🚀 Starting Health Check Panel...$(NC)"
	@echo ""
	@$(MAKE) -s db-up
	@sleep 3
	@echo ""
	@echo "$(YELLOW)Starting backend in background...$(NC)"
	@cd backend && . venv/bin/activate && uvicorn app.main:app --reload --port 8000 > /tmp/healthcheck-backend.log 2>&1 &
	@sleep 2
	@echo "$(GREEN)✓ Backend started: http://localhost:8000$(NC)"
	@echo ""
	@echo "$(YELLOW)Starting frontend (interactive mode)...$(NC)"
	@echo "$(BLUE)Frontend: http://localhost:3000$(NC)"
	@echo "$(GREEN)Press Ctrl+C to stop$(NC)"
	@echo ""
	@cd frontend && npm run dev

down: ## Stop all services
	@echo "$(BLUE)🛑 Stopping all services...$(NC)"
	@docker-compose down
	@pkill -f "uvicorn app.main:app" || true
	@pkill -f "next dev" || true
	@echo "$(GREEN)✓ All services stopped$(NC)"

install: install-backend install-frontend ## Install all dependencies (backend + frontend)
	@echo "$(GREEN)✓ All dependencies installed$(NC)"

install-backend: ## Install backend dependencies
	@echo "$(BLUE)Installing backend dependencies...$(NC)"
	@cd backend && \
		([ -d venv ] || python3 -m venv venv) && \
		. venv/bin/activate && \
		pip install --upgrade pip -q && \
		pip install -r requirements.txt -q
	@echo "$(GREEN)✓ Backend dependencies installed$(NC)"

install-frontend: ## Install frontend dependencies (Astro)
	@echo "$(BLUE)Installing frontend dependencies (Astro)...$(NC)"
	@cd frontend && npm install
	@echo "$(GREEN)✓ Frontend dependencies installed$(NC)"

db-up: ## Start only PostgreSQL database
	@echo "$(BLUE)📦 Starting PostgreSQL...$(NC)"
	@docker-compose up -d postgres
	@echo "$(YELLOW)Waiting for database to be ready...$(NC)"
	@sleep 5
	@echo "$(GREEN)✓ PostgreSQL started$(NC)"

db-down: ## Stop PostgreSQL database
	@echo "$(BLUE)Stopping PostgreSQL...$(NC)"
	@docker-compose down
	@echo "$(GREEN)✓ PostgreSQL stopped$(NC)"

db-reset: ## Reset database (delete all data)
	@echo "$(RED)⚠️  This will delete ALL data!$(NC)"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@docker-compose down -v
	@$(MAKE) db-up
	@sleep 3
	@$(MAKE) migrate
	@echo "$(GREEN)✓ Database reset complete$(NC)"

migrate: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(NC)"
	@cd backend && . venv/bin/activate && alembic upgrade head
	@echo "$(GREEN)✓ Migrations complete$(NC)"

seed: ## Create default admin user (admin@admin.com / admin)
	@echo "$(BLUE)Seeding database...$(NC)"
	@cd backend && . venv/bin/activate && PYTHONPATH=. python app/seed.py
	@echo "$(GREEN)✓ Database seeded$(NC)"

setup: install db-up migrate seed ## Complete first-time setup (install + db + migrate + seed)
	@echo ""
	@echo "$(GREEN)========================================$(NC)"
	@echo "$(GREEN)✅ Setup Complete!$(NC)"
	@echo "$(GREEN)========================================$(NC)"
	@echo ""
	@echo "$(BLUE)Default Admin Credentials:$(NC)"
	@echo "  Email:    admin@admin.com"
	@echo "  Password: admin"
	@echo ""
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. Start services: make up-bg"
	@echo "  2. Open browser: http://localhost:3000"
	@echo "  3. Login with admin credentials"
	@echo ""

migrate-create: ## Create a new migration (use: make migrate-create MSG="your message")
	@cd backend && . venv/bin/activate && alembic revision --autogenerate -m "$(MSG)"

backend: ## Start only backend
	@echo "$(BLUE)🔧 Starting backend...$(NC)"
	@echo "$(YELLOW)Backend: http://localhost:8000$(NC)"
	@echo "$(YELLOW)API Docs: http://localhost:8000/api/docs$(NC)"
	@echo ""
	@cd backend && . venv/bin/activate && uvicorn app.main:app --reload --port 8000

frontend: ## Start only frontend
	@echo "$(BLUE)🎨 Starting frontend...$(NC)"
	@echo "$(YELLOW)Frontend: http://localhost:3000$(NC)"
	@echo ""
	@cd frontend && npm run dev

test: ## Run API tests
	@echo "$(BLUE)🧪 Running API tests...$(NC)"
	@./test_api.sh

test-backend: ## Test backend health
	@echo "$(BLUE)Testing backend...$(NC)"
	@curl -s http://localhost:8000/health | jq || echo "$(RED)Backend not running$(NC)"

test-frontend: ## Test frontend
	@echo "$(BLUE)Testing frontend...$(NC)"
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 | grep -q 200 && echo "$(GREEN)Frontend is running$(NC)" || echo "$(RED)Frontend not running$(NC)"

logs: ## Show logs from all services
	@docker-compose logs -f

logs-db: ## Show PostgreSQL logs
	@docker-compose logs -f postgres

status: ## Show status of all services
	@echo "$(BLUE)Service Status:$(NC)"
	@echo ""
	@echo -n "PostgreSQL:  "
	@docker-compose ps postgres | grep -q Up && echo "$(GREEN)Running$(NC)" || echo "$(RED)Stopped$(NC)"
	@echo -n "Backend:     "
	@curl -s http://localhost:8000/health > /dev/null 2>&1 && echo "$(GREEN)Running$(NC)" || echo "$(RED)Stopped$(NC)"
	@echo -n "Frontend:    "
	@curl -s -o /dev/null http://localhost:3000 2>&1 && echo "$(GREEN)Running$(NC)" || echo "$(RED)Stopped$(NC)"
	@echo ""

clean: ## Clean all generated files and dependencies
	@echo "$(BLUE)🧹 Cleaning...$(NC)"
	@rm -rf backend/venv
	@rm -rf backend/__pycache__
	@rm -rf backend/app/__pycache__
	@find backend -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf frontend/node_modules
	@rm -rf frontend/.next
	@echo "$(GREEN)✓ Cleaned$(NC)"

build-frontend: ## Build frontend for production
	@echo "$(BLUE)📦 Building frontend...$(NC)"
	@cd frontend && npm run build
	@echo "$(GREEN)✓ Frontend built$(NC)"

dev: up ## Alias for 'make up'

prod-backend: ## Run backend in production mode
	@cd backend && . venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000

prod-frontend: ## Run frontend in production mode
	@cd frontend && npm run build && npm start

docker-build: ## Build Docker image for production
	@echo "$(BLUE)🐳 Building Docker image...$(NC)"
	@docker build -t healthcheck-panel:latest .
	@echo "$(GREEN)✓ Docker image built$(NC)"

docker-run: ## Run production Docker image
	@docker run -p 8000:8000 --env-file backend/.env healthcheck-panel:latest

shell-backend: ## Open Python shell in backend environment
	@cd backend && . venv/bin/activate && python

shell-db: ## Open PostgreSQL shell
	@docker exec -it websitehealthcheckpanel-postgres-1 psql -U healthcheck -d healthcheck

info: ## Show project information
	@echo "$(BLUE)Health Check Panel$(NC)"
	@echo "=================="
	@echo ""
	@echo "$(GREEN)URLs:$(NC)"
	@echo "  Frontend:  http://localhost:3000"
	@echo "  Backend:   http://localhost:8000"
	@echo "  API Docs:  http://localhost:8000/api/docs"
	@echo ""
	@echo "$(GREEN)Database:$(NC)"
	@echo "  Host:      localhost"
	@echo "  Port:      5432"
	@echo "  Database:  healthcheck"
	@echo "  User:      healthcheck"
	@echo "  Password:  dev123"
	@echo ""
	@echo "$(GREEN)Commands:$(NC)"
	@echo "  make up      - Start everything"
	@echo "  make down    - Stop everything"
	@echo "  make status  - Check service status"
	@echo "  make help    - Show all commands"
	@echo ""
