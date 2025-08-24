.PHONY: help install install-dev test test-cov lint format clean build publish

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install taskpods in development mode
	pip install -e .

install-dev: ## Install development dependencies
	pip install -e ".[dev]"
	pre-commit install

test: ## Run tests
	pytest tests/ -v

test-cov: ## Run tests with coverage
	pytest tests/ --cov=taskpods --cov-report=html --cov-report=term

lint: ## Run linting checks
	flake8 taskpods.py tests/ --max-line-length=88 --extend-ignore=E203,W503,E501,E402
	mypy taskpods.py

format: ## Format code with black and isort
	black taskpods.py tests/
	isort taskpods.py tests/

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

build: ## Build distribution packages
	python -m build

publish: ## Publish to PyPI (requires twine)
	twine upload dist/*

check: ## Run all quality checks
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) format

dev-setup: ## Set up development environment
	$(MAKE) install-dev
	$(MAKE) check
