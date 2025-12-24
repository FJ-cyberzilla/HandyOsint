.PHONY: install setup test lint format typecheck clean run build security db-init db-backup help hooks docs

all: install

install:
	pip install -r config/requirements.txt
	pip install -r config/requirements-dev.txt

setup: install
	cp -n .env.example .env || true
	python -m pip install --upgrade pip
	pre-commit install

lint:
	nox -s lint

test:
	nox -s tests

format:
	nox -s format

typecheck:
	nox -s typecheck

security:
	nox -s safety

docs:
	nox -s docs

run:
	python main.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +

build: clean
	python setup.py sdist bdist_wheel

db-init:
	python -c "from main import DatabaseManager; DatabaseManager(); print('Database initialized')"

db-backup:
	cp data/social_scan.db backups/social_scan_$(shell date +%Y%m%d_%H%M%S).db

hooks:
	pre-commit install

help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make setup         - Development setup"
	@echo "  make lint          - Run linting (via Nox)"
	@echo "  make test          - Run tests (via Nox)"
	@echo "  make format        - Format code (via Nox)"
	@echo "  make typecheck     - Run mypy (via Nox)"
	@echo "  make security      - Security checks (via Nox)"
	@echo "  make docs          - Build docs (via Nox)"
	@echo "  make run           - Run application"
	@echo "  make clean         - Clean up"
	@echo "  make build         - Build distribution"
	@echo "  make db-init       - Initialize database"
	@echo "  make db-backup     - Backup database"
	@echo "  make hooks         - Install pre-commit hooks"
