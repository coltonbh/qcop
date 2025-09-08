#!/bin/sh

set -e
# Run tests
# First command-line argument
arg=$1

# Run tests
if [ "$arg" = "--integration" ]; then
    # Run all tests including integration tests
    uv run pytest -m 'not not_integration' --cov-report=term-missing --cov-report html:htmlcov --cov-config=pyproject.toml --cov=qcop --cov=tests .
else
    # Run tests excluding integration tests
    uv run pytest --cov-report=term-missing --cov-report html:htmlcov --cov-config=pyproject.toml --cov=qcop --cov=tests .
fi