"""
Database utility functions for SCIRAG.
"""

from typing import Optional, Type, TypeVar, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")


def get_or_create(
    db: Session,
    model: Type[T],
    defaults: Optional[Dict[str, Any]] = None,
    **kwargs
) -> tuple[T, bool]:
    """
    Get an existing object or create a new one.
    
    Args:
        db: Database session
        model: SQLAlchemy model class
        defaults: Default values for creation
        **kwargs: Fields to filter by
        
    Returns:
        Tuple of (instance, created) where created is True if a new instance was created
    """
    instance = db.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    
    params = dict(kwargs)
    if defaults:
        params.update(defaults)
    
    instance = model(**params)
    db.add(instance)
    try:
        db.commit()
        db.refresh(instance)
        return instance, True
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error creating {model.__name__}: {e}")
        raise


def update_or_create(
    db: Session,
    model: Type[T],
    defaults: Dict[str, Any],
    **kwargs
) -> tuple[T, bool]:
    """
    Update an existing object or create a new one.
    
    Args:
        db: Database session
        model: SQLAlchemy model class
        defaults: Values to update/create with
        **kwargs: Fields to filter by
        
    Returns:
        Tuple of (instance, created) where created is True if a new instance was created
    """
    instance = db.query(model).filter_by(**kwargs).first()
    
    if instance:
        # Update existing instance
        for key, value in defaults.items():
            setattr(instance, key, value)
        
        try:
            db.commit()
            db.refresh(instance)
            return instance, False
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating {model.__name__}: {e}")
            raise
    else:
        # Create new instance
        params = dict(kwargs)
        params.update(defaults)
        instance = model(**params)
        db.add(instance)
        
        try:
            db.commit()
            db.refresh(instance)
            return instance, True
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error creating {model.__name__}: {e}")
            raise


def bulk_create(
    db: Session,
    model: Type[T],
    objects: List[Dict[str, Any]]
) -> List[T]:
    """
    Bulk create multiple objects.
    
    Args:
        db: Database session
        model: SQLAlchemy model class
        objects: List of dictionaries containing object data
        
    Returns:
        List of created instances
    """
    instances = [model(**obj) for obj in objects]
    db.add_all(instances)
    
    try:
        db.commit()
        return instances
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error bulk creating {model.__name__}: {e}")
        raise


def paginate(
    query,
    page: int = 1,
    page_size: int = 10,
    order_by=None,
    order_direction: str = "desc"
) -> Dict[str, Any]:
    """
    Paginate a query.
    
    Args:
        query: SQLAlchemy query
        page: Page number (1-indexed)
        page_size: Items per page
        order_by: Column to order by
        order_direction: "asc" or "desc"
        
    Returns:
        Dictionary with pagination info and items
    """
    if order_by is not None:
        if order_direction == "desc":
            query = query.order_by(desc(order_by))
        else:
            query = query.order_by(asc(order_by))
    
    total = query.count()
    
    if page_size > 0:
        query = query.offset((page - 1) * page_size).limit(page_size)
    
    items = query.all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 1,
    }


def safe_commit(db: Session) -> bool:
    """
    Safely commit a database session.
    
    Args:
        db: Database session
        
    Returns:
        True if commit succeeded, False otherwise
    """
    try:
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database commit failed: {e}")
        return False