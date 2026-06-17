.PHONY: help install install-dev test test-cov test-unit test-integration test-smoke clean lint format

PYTHON := python3
PIP := $(PYTHON) -m pip
PYTEST := $(PYTHON) -m pytest
PROJECT_NAME := digital-auditor

help:
	@echo "$(PROJECT_NAME) - Development Commands"
	@echo ""
	@echo "Installation:"
	@echo "  make install              Install package with production dependencies"
	@echo "  make install-dev          Install package with development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test                 Run all unit + smoke tests (requires setup.py)"
	@echo "  make test-cov             Run tests with coverage report"
	@echo "  make test-unit            Run unit tests only"
	@echo "  make test-smoke           Run smoke tests only"
	@echo "  make test-integration     Run integration tests (requires real Ollama)"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint                 Check code with flake8"
	@echo "  make format               Format code with black"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean                Remove build artifacts and cache files"
	@echo ""

install:
	$(PIP) install -e .

install-dev:
	$(PIP) install -e ".[dev]"

test:
	$(PYTEST) tests/unit tests/smoke -v --tb=short

test-cov:
	$(PYTEST) tests/unit tests/smoke -v --cov=. --cov-report=term-missing --cov-report=html

test-unit:
	$(PYTEST) tests/unit -v -m unit --tb=short

test-smoke:
	$(PYTEST) tests/smoke -v -m smoke --tb=short

test-integration:
	@echo "Running integration tests with real Ollama..."
	$(PYTEST) tests/integration -v -m integration --tb=short

clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .eggs/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*~" -delete
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .tox/
	@echo "Clean complete."

lint:
	$(PYTHON) -m flake8 core agents tasks knowledge tools report_generator --max-line-length=100

format:
	$(PYTHON) -m black core agents tasks knowledge tools report_generator tests

.DEFAULT_GOAL := help
