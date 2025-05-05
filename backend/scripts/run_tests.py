"""
Script to run tests with SQLite in-memory database.
"""

import os
import sys
import pytest

# Add the backend directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

def main():
    """Run tests with SQLite in-memory database."""
    # Set environment variable to use SQLite for testing
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    
    # Run pytest
    sys.exit(pytest.main(["-v", "tests/"]))

if __name__ == "__main__":
    main()