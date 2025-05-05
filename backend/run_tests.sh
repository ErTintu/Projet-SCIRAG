#!/bin/bash

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "../.venv" ]; then
    source ../.venv/bin/activate
fi

# Set environment variable to use SQLite for testing
export DATABASE_URL="sqlite:///:memory:"

# Run tests
pytest tests/ -v