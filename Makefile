.PHONY: help up down logs migrate seed test-unit test-api lint frontend-dev backend-dev clean

help:
	@echo ""
	@echo "WifiPlan — Development Commands"
	@echo "================================"
	@echo "  make up            Start all services (Docker Compose)"
	@echo "  make down          Stop all services"
	@echo "  make logs          Tail logs for all services"
	@echo "  make migrate       Run Alembic DB migrations"
	@echo "  make seed          Seed demo data (AP catalog + demo user)"
	@echo "  make test-unit     Run unit tests (RF engine + CV pipeline, no DB)"
	@echo "  make test-api      Run API integration tests (requires Postgres)"
	@echo "  make lint          Run backend linting"
	@echo "  make frontend-dev  Start Next.js dev server only"
	@echo "  make backend-dev   Start FastAPI dev server only"
	@echo "  make clean         Remove containers, volumes, caches"
	@echo ""

# ── Docker ────────────────────────────────────────────────────────────────────
up:
	test -f .env || cp .env.example .env
	docker compose up -d --build
	@echo "\n✅ Services starting..."
	@echo "  API:      http://localhost:8000/docs"
	@echo "  Frontend: http://localhost:3000"
	@echo "  MinIO:    http://localhost:9001 (minioadmin/minioadmin)"
	@echo ""
	@echo "Run 'make migrate && make seed' after first startup"

down:
	docker compose down

logs:
	docker compose logs -f backend worker frontend

# ── Database ──────────────────────────────────────────────────────────────────
migrate:
	cd backend && alembic upgrade head

seed:
	cd backend && python -m app.seeds.run

# ── Tests ─────────────────────────────────────────────────────────────────────
test-unit:
	cd backend && python -m pytest tests/test_rf_engine.py tests/test_cv_pipeline.py -v

test-api:
	@echo "Requires PostgreSQL running (make up or docker compose up postgres -d)"
	cd backend && python -m pytest tests/test_auth.py tests/test_projects.py tests/test_geometry.py -v

test-all:
	cd backend && python -m pytest tests/ -v

# ── Local dev (without Docker) ────────────────────────────────────────────────
backend-dev:
	cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

worker-dev:
	cd backend && celery -A app.workers.celery_app worker --loglevel=info -Q cv_pipeline,rf_engine

frontend-dev:
	cd frontend && npm run dev

# ── Lint ──────────────────────────────────────────────────────────────────────
lint:
	cd backend && python -m ruff check app/ tests/
	cd frontend && npm run lint

# ── Clean ─────────────────────────────────────────────────────────────────────
clean:
	docker compose down -v --remove-orphans
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	cd frontend && rm -rf .next node_modules 2>/dev/null || true
