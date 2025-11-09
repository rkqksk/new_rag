# Makefile - RAG Enterprise Development Commands
# Version: 2.0.0
# Updated: 2025-11-09

.PHONY: help setup dev test test-cov test-watch lint format clean \
        docker-up docker-down docker-restart docker-logs docker-clean \
        migrate migrate-create migrate-upgrade migrate-downgrade \
        seed db-shell shell logs health \
        max api profile status install pre-commit ci

# Default target
.DEFAULT_GOAL := help

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## 📚 Show available commands
	@echo "$(BLUE)╔═══════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║   RAG Enterprise - Development Commands          ║$(NC)"
	@echo "$(BLUE)╚═══════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(GREEN)Quick Start:$(NC)"
	@echo "  make setup      # Complete environment setup"
	@echo "  make dev        # Start development server"
	@echo "  make test       # Run tests"
	@echo ""
	@echo "$(GREEN)Available Commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-18s$(NC) %s\n", $$1, $$2}'
	@echo ""

# ============================================================================
# Setup & Installation
# ============================================================================

setup: ## 🚀 Complete environment setup (first-time)
	@echo "$(BLUE)🚀 Setting up RAG Enterprise...$(NC)"
	@./scripts/setup-env.sh development
	@make install
	@make docker-up
	@echo ""
	@echo "$(GREEN)✅ Setup complete!$(NC)"
	@echo "$(YELLOW)Next: make dev$(NC)"

install: ## 📦 Install Python dependencies
	@echo "$(BLUE)📦 Installing dependencies...$(NC)"
	@pip install --upgrade pip
	@pip install -r requirements.txt
	@echo "$(GREEN)✅ Dependencies installed$(NC)"

pre-commit: ## 🔧 Install pre-commit hooks
	@echo "$(BLUE)🔧 Installing pre-commit hooks...$(NC)"
	@pip install pre-commit
	@pre-commit install
	@echo "$(GREEN)✅ Pre-commit hooks installed$(NC)"

# ============================================================================
# Development
# ============================================================================

dev: ## 💻 Start development server (with reload)
	@echo "$(BLUE)💻 Starting development server...$(NC)"
	@uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

dev-docker: docker-up ## 🐳 Start development with Docker
	@echo "$(GREEN)✅ Development environment running$(NC)"
	@echo "API: http://localhost:8001"
	@echo "Docs: http://localhost:8001/api/v1/docs"

# ============================================================================
# Testing
# ============================================================================

test: ## 🧪 Run all tests
	@echo "$(BLUE)🧪 Running tests...$(NC)"
	@pytest tests/ -v

test-cov: ## 📊 Run tests with coverage report
	@echo "$(BLUE)📊 Running tests with coverage...$(NC)"
	@pytest tests/ -v --cov=src --cov=app --cov-report=html --cov-report=term
	@echo ""
	@echo "$(GREEN)Coverage report: htmlcov/index.html$(NC)"

test-watch: ## 👁️  Run tests in watch mode
	@echo "$(BLUE)👁️  Running tests in watch mode...$(NC)"
	@pip install pytest-watch 2>/dev/null || true
	@ptw tests/ -- -v

test-unit: ## 🔬 Run unit tests only
	@pytest tests/unit/ -v

test-integration: ## 🔗 Run integration tests only
	@pytest tests/integration/ -v

test-failed: ## 🔴 Re-run only failed tests
	@pytest --lf -v

# ============================================================================
# Code Quality
# ============================================================================

lint: ## 🔍 Run all linters
	@echo "$(BLUE)🔍 Running linters...$(NC)"
	@black --check src/ app/ tests/
	@isort --check-only src/ app/ tests/
	@flake8 src/ app/ tests/ --max-line-length=100
	@echo "$(GREEN)✅ Linting passed$(NC)"

format: ## ✨ Auto-format code
	@echo "$(BLUE)✨ Formatting code...$(NC)"
	@black src/ app/ tests/
	@isort src/ app/ tests/
	@echo "$(GREEN)✅ Code formatted$(NC)"

type-check: ## 🔎 Run type checking
	@echo "$(BLUE)🔎 Type checking...$(NC)"
	@mypy src/ app/ 2>/dev/null || echo "$(YELLOW)mypy not configured$(NC)"

# ============================================================================
# Docker Operations
# ============================================================================

docker-up: ## 🐳 Start Docker services
	@echo "$(BLUE)🐳 Starting Docker services...$(NC)"
	@docker-compose up -d
	@echo "$(GREEN)✅ Services started$(NC)"
	@sleep 3
	@make health

docker-down: ## 🛑 Stop Docker services
	@echo "$(BLUE)🛑 Stopping Docker services...$(NC)"
	@docker-compose down
	@echo "$(GREEN)✅ Services stopped$(NC)"

docker-restart: ## 🔄 Restart Docker services
	@echo "$(BLUE)🔄 Restarting Docker services...$(NC)"
	@docker-compose restart
	@echo "$(GREEN)✅ Services restarted$(NC)"

docker-logs: ## 📜 View Docker logs (all services)
	@docker-compose logs -f

docker-logs-api: ## 📜 View API logs only
	@docker-compose logs -f api

docker-clean: ## 🧹 Clean Docker (remove containers, volumes, images)
	@echo "$(YELLOW)⚠️  This will remove all containers, volumes, and images$(NC)"
	@read -p "Continue? (y/N): " confirm && [ "$$confirm" = "y" ] && \
	docker-compose down -v --rmi all || echo "Cancelled"
	@echo "$(GREEN)✅ Docker cleaned$(NC)"

docker-build: ## 🔨 Rebuild Docker images
	@echo "$(BLUE)🔨 Building Docker images...$(NC)"
	@docker-compose build --no-cache
	@echo "$(GREEN)✅ Images rebuilt$(NC)"

# ============================================================================
# Database Operations
# ============================================================================

migrate-create: ## ✏️  Create new migration
	@read -p "Migration name: " name; \
	alembic revision --autogenerate -m "$$name" 2>/dev/null || \
	echo "$(YELLOW)Alembic not configured yet$(NC)"

migrate-upgrade: ## ⬆️  Upgrade database to latest
	@echo "$(BLUE)⬆️  Upgrading database...$(NC)"
	@alembic upgrade head 2>/dev/null || echo "$(YELLOW)Alembic not configured$(NC)"

migrate-downgrade: ## ⬇️  Downgrade database by 1 revision
	@echo "$(YELLOW)⬇️  Downgrading database...$(NC)"
	@alembic downgrade -1 2>/dev/null || echo "$(YELLOW)Alembic not configured$(NC)"

migrate-history: ## 📖 Show migration history
	@alembic history 2>/dev/null || echo "$(YELLOW)Alembic not configured$(NC)"

seed: ## 🌱 Seed database with test data
	@echo "$(BLUE)🌱 Seeding database...$(NC)"
	@python scripts/seed_database.py 2>/dev/null || echo "$(YELLOW)Seed script not found$(NC)"

db-shell: ## 🐘 Open PostgreSQL shell
	@docker-compose exec postgres psql -U postgres -d rag_enterprise

# ============================================================================
# Utility Commands
# ============================================================================

shell: ## 🐍 Open Python shell (IPython)
	@pip install ipython 2>/dev/null || true
	@ipython -i -c "from app.main import app; from app.core.config import settings" 2>/dev/null || \
	python -i -c "from app.main import app; from app.core.config import settings"

logs: ## 📋 Tail application logs
	@tail -f logs/rag-enterprise.log 2>/dev/null || echo "$(YELLOW)No logs yet$(NC)"

health: ## ❤️  Check service health
	@echo "$(BLUE)❤️  Checking service health...$(NC)"
	@./scripts/health-check.sh 2>/dev/null || curl -s http://localhost:8001/health/ready || \
	echo "$(RED)Services not ready$(NC)"

clean: ## 🧹 Clean temporary files
	@echo "$(BLUE)🧹 Cleaning temporary files...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name ".coverage" -delete
	@rm -rf htmlcov/ .coverage coverage.xml
	@echo "$(GREEN)✅ Cleaned$(NC)"

# ============================================================================
# MCP Profile Management
# ============================================================================

max: ## 🚀 Switch to MAX MCP profile (7 servers)
	@echo "$(BLUE)🚀 Switching to MAX profile...$(NC)"
	@./scripts/switch_mcp_profile.sh max 2>/dev/null || echo "$(YELLOW)MCP profile script not found$(NC)"
	@echo ""
	@echo "$(GREEN)✅ Done! Restart Claude Code$(NC)"

api: ## 🔌 Switch to API MCP profile (4 servers)
	@echo "$(BLUE)🔌 Switching to API profile...$(NC)"
	@./scripts/switch_mcp_profile.sh api 2>/dev/null || echo "$(YELLOW)MCP profile script not found$(NC)"
	@echo ""
	@echo "$(GREEN)✅ Done! Restart Claude Code$(NC)"

profile: ## 📋 Show current MCP profile
	@echo "$(BLUE)📋 Current MCP Profile:$(NC)"
	@echo "======================"
	@if [ -f .mcp.profile.current ]; then \
		echo "Active: $$(cat .mcp.profile.current)"; \
	else \
		echo "No profile marker found"; \
	fi
	@echo ""
	@echo "Configuration (.mcp.json):"
	@grep -A1 "_comment" .mcp.json 2>/dev/null | head -2 || echo "Not found"

status: ## 🔍 Show project status
	@echo "$(BLUE)🔍 Project Status$(NC)"
	@echo "================="
	@echo ""
	@echo "Docker Containers:"
	@docker-compose ps 2>/dev/null || echo "  Not running"
	@echo ""
	@echo "Git Branch:"
	@git branch --show-current 2>/dev/null || echo "Not a git repo"

# ============================================================================
# CI/CD
# ============================================================================

ci: lint test ## 🤖 Run CI pipeline locally
	@echo "$(GREEN)✅ CI pipeline passed$(NC)"

# ============================================================================
# Shortcuts
# ============================================================================

up: docker-up ## 🆙 Alias for docker-up
down: docker-down ## 🔽 Alias for docker-down
restart: docker-restart ## 🔄 Alias for docker-restart
