.PHONY: help up backend frontend db migrate seed setup down status

GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m

.DEFAULT_GOAL := help

help: ## Show commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-12s$(NC) %s\n", $$1, $$2}'

up: db ## Start all services
	@echo "$(GREEN)Starting backend...$(NC)"
	@cd backend && . venv/bin/activate && uvicorn app.main:app --reload --port 8000 > /tmp/healthcheck-backend.log 2>&1 &
	@sleep 2
	@echo "$(GREEN)Starting frontend...$(NC)"
	@cd frontend && npm run dev > /tmp/healthcheck-frontend.log 2>&1 &
	@sleep 2
	@echo ""
	@echo "$(GREEN)✅ All services running$(NC)"
	@echo ""
	@echo "Frontend:  http://localhost:3000"
	@echo "Backend:   http://localhost:8000"
	@echo "API Docs:  http://localhost:8000/docs"
	@echo ""
	@echo "Logs:"
	@echo "  Backend:  tail -f /tmp/healthcheck-backend.log"
	@echo "  Frontend: tail -f /tmp/healthcheck-frontend.log"
	@echo ""
	@echo "$(YELLOW)Stop with: make down$(NC)"
	@echo ""

setup: ## First-time setup
	@echo "Installing backend..."
	@cd backend && ([ -d venv ] || python3 -m venv venv) && \
		. venv/bin/activate && \
		pip install -q --upgrade pip && \
		pip install -q -r requirements.txt
	@echo "Installing frontend..."
	@cd frontend && npm install -s
	@echo "Starting database..."
	@docker-compose up -d postgres && sleep 3
	@echo "Running migrations..."
	@cd backend && . venv/bin/activate && alembic upgrade head
	@echo "Creating admin user..."
	@cd backend && . venv/bin/activate && PYTHONPATH=. python app/seed.py
	@echo ""
	@echo "$(GREEN)✅ Setup complete!$(NC)"
	@echo ""
	@echo "Login: admin@admin.com / adminadmin"
	@echo ""
	@echo "$(YELLOW)Start servers:$(NC)"
	@echo "  make backend"
	@echo "  make frontend"
	@echo ""

backend: ## Start backend
	@cd backend && ./venv/bin/uvicorn app.main:app --reload --port 8000

frontend: ## Start frontend
	@cd frontend && npm run dev

db: ## Start database
	@docker-compose up -d postgres && sleep 2
	@echo "$(GREEN)✓ PostgreSQL running on port 5433$(NC)"

migrate: ## Run migrations
	@cd backend && . venv/bin/activate && alembic upgrade head

seed: ## Create admin user
	@cd backend && . venv/bin/activate && PYTHONPATH=. python app/seed.py

down: ## Stop all services
	@docker-compose down
	@pkill -f "uvicorn app.main:app" || true
	@pkill -f "npm run dev" || true
	@echo "$(GREEN)✓ Stopped$(NC)"

status: ## Check services
	@echo -n "Database: "
	@docker-compose ps postgres | grep -q Up && echo "$(GREEN)Running$(NC)" || echo "Stopped"
	@echo -n "Backend:  "
	@curl -s http://localhost:8000/health > /dev/null 2>&1 && echo "$(GREEN)Running$(NC)" || echo "Stopped"
	@echo -n "Frontend: "
	@curl -s -o /dev/null http://localhost:3000 2>&1 && echo "$(GREEN)Running$(NC)" || echo "Stopped"
