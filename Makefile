.PHONY: help install install-dev test test-cov test-fast lint format check clean build publish docs security

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install:  ## Install the package
	pip install -e .

install-dev:  ## Install development dependencies
	pip install -e ".[dev]"

test:  ## Run all tests
	pytest

test-cov:  ## Run tests with coverage
	pytest --cov=taskpods --cov-report=html --cov-report=term-missing

test-fast:  ## Run tests in parallel
	pytest -n auto

lint:  ## Run all linters
	flake8 . --max-line-length=88 --extend-ignore=E203,W503,E402 --exclude=.taskpods,dist,build,__pycache__
	mypy taskpods.py
	black --check --diff .

format:  ## Format code with Black
	black .
	isort .

check: format lint test  ## Run all quality checks

clean:  ## Clean up build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build:  ## Build the package
	python -m build

publish:  ## Publish to PyPI (requires PYPI_API_TOKEN)
	twine upload dist/*

# docs:  ## Build documentation (requires sphinx - removed for Python 3.9 compatibility)
# 	sphinx-build -b html docs/ docs/_build/html

security:  ## Run security checks
	bandit -r . --exclude tests,.taskpods,dist,build,__pycache__ --skip B101,B108,B404,B603,B607,B110
	safety check

pre-commit:  ## Install pre-commit hooks
	pre-commit install

pre-commit-run:  ## Run pre-commit on all files
	pre-commit run --all-files
