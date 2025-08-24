.PHONY: help install install-dev test test-cov test-fast lint format check clean build publish release release-patch release-minor release-major release-custom docs security pre-commit pre-commit-run

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
	flake8 . --max-line-length=88 --extend-ignore=E203,W503,E501,E402,D103 --exclude=.taskpods,dist,build,__pycache__
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

release: ## Interactive release with version management
	@echo "🚀 Starting interactive release process..."
	@echo "Available options:"
	@echo "  make release-patch    # Release patch version (0.1.0 -> 0.1.1)"
	@echo "  make release-minor    # Release minor version (0.1.0 -> 0.2.0)"
	@echo "  make release-major    # Release major version (0.1.0 -> 1.0.0)"
	@echo "  make release-custom   # Release with custom version"

release-patch: ## Release patch version
	python scripts/release.py --type patch

release-minor: ## Release minor version
	python scripts/release.py --type minor

release-major: ## Release major version
	python scripts/release.py --type major

release-custom: ## Release with custom version
	@read -p "Enter version (e.g., 0.2.0): " version; \
	read -p "Enter description (optional): " description; \
	python scripts/release.py --version $$version --description "$$description"

# docs:  ## Build documentation (requires sphinx - removed for Python 3.9 compatibility)
# 	sphinx-build -b html docs/ docs/_build/html

security:  ## Run security checks
	bandit -r . --exclude tests,.taskpods,dist,build,__pycache__ --skip B101,B108,B404,B603,B607,B110
	safety check

pre-commit:  ## Install pre-commit hooks
	pre-commit install

pre-commit-run:  ## Run pre-commit on all files
	pre-commit run --all-files
