.PHONY: help install test lint type check docs clean install-dev format security-test

# Default target
help:
	@echo "Health Economic Evaluation Toolkit - Development Commands"
	@echo ""
	@echo "Usage:"
	@echo "  make install      - Install the package in development mode"
	@echo "  make install-dev  - Install the package with development dependencies"
	@echo "  make test         - Run all tests"
	@echo "  make unit-test    - Run unit tests only"
	@echo "  make integration-test - Run integration tests only"
	@echo "  make lint         - Run linting checks"
	@echo "  make type         - Run type checking"
	@echo "  make check        - Run both linting and type checking"
	@echo "  make format       - Format all code with black and isort"
	@echo "  make docs         - Build documentation"
	@echo "  make clean        - Clean all build artifacts"
	@echo "  make security-test - Run security scans"
	@echo "  make pre-commit   - Run all pre-commit hooks"
	@echo ""

# Install the package in development mode
install:
	pip install -e .

# Install the package with development dependencies
install-dev:
	pip install -r requirements.txt
	pip install -e .

# Run all tests
test:
	pytest tests/ -v --tb=short

# Run unit tests only
unit-test:
	pytest tests/unit/ -v --tb=short

# Run integration tests only
integration-test:
	pytest tests/integration/ -v --tb=short

# Run performance tests
perf-test:
	pytest tests/performance/ -v --tb=short

# Run linting checks
lint:
	flake8 scripts analysis tests

# Run type checking
type:
	mypy --config-file setup.cfg scripts analysis tests

# Run both linting and type checking
check: lint type

# Format all code
format:
	black scripts analysis tests
	isort --profile black scripts analysis tests

# Build documentation
docs:
	cd docs && make html

# Clean all build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf .tox/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Run security tests
security-test:
	bandit -r scripts analysis -ll
	safety check -r requirements.txt

# Run all pre-commit checks
pre-commit: format lint type security-test

# Run tox
tox:
	tox

# Run coverage
coverage:
	pytest --cov=scripts --cov-report=html --cov-report=xml --cov-report=term tests/

# Run all tests with coverage
test-cov: coverage test

# Install and set up pre-commit hooks
setup-hooks:
	pre-commit install

# Update pre-commit hooks
update-hooks:
	pre-commit autoupdate