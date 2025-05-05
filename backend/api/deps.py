"""
Shared dependencies for API routes.
"""

from typing import Generator
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.connection import get_db, SessionLocal


# Database dependency
def get_db_session() -> Generator[Session, None, None]:
    """
    Dependency to get a database session.
    
    Yields:
        SQLAlchemy Session: Database session.
    """
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


# Model retrieval utilities with proper error handling
def get_model_by_id(db: Session, model, model_id: int, error_message: str = None):
    """
    Get a model instance by ID with proper error handling.
    
    Args:
        db: Database session
        model: SQLAlchemy model class
        model_id: ID to look up
        error_message: Custom error message (optional)
        
    Returns:
        Model instance
        
    Raises:
        HTTPException: If model not found
    """
    instance = db.query(model).filter(model.id == model_id).first()
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_message or f"{model.__name__} with ID {model_id} not found"
        )
    return instance