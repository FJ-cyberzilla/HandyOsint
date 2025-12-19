.PHONY: install test lint format clean run setup

# Default target
all: install

# Install dependencies
install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

# Development setup
setup: install
	cp .env.example .env
	python -m pip install --upgrade pip
	pre-commit install

# Run tests
test:
	python -m pytest tests/ -v --cov=.

# Run linting
lint:
	flake8 .
	black --check .
	isort --check-only .

# Format code
format:
	black .
	isort .

# Run the application
run:
	python main.py

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +

# Production build
build: clean
	python setup.py sdist bdist_wheel

# Security check
security:
	bandit -r .
	safety check

# Database management
db-init:
	python -c "from core.production_scanner import ProductionScanner; s = ProductionScanner(); print('Database initialized')"

db-backup:
	cp data/social_scan.db backups/social_scan_$(shell date +%Y%m%d_%H%M%S).db

# Help
help:
	@echo "Available commands:"
	@echo "  make install     - Install dependencies"
	@echo "  make setup       - Development setup"
	@echo "  make test        - Run tests"
	@echo "  make lint        - Run linting"
	@echo "  make format      - Format code"
	@echo "  make run         - Run application"
	@echo "  make clean       - Clean up"
	@echo "  make build       - Build distribution"
	@echo "  make security    - Security checks"
	@echo "  make db-init     - Initialize database"
	@echo "  make db-backup   - Backup database"
