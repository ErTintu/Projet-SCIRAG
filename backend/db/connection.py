"""
Database connection management for SCIRAG.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/scirag")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    """
    Dependency function for FastAPI to get database session.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initialize database by creating all tables.
    Should be called on application startup.
    """
    from db.models import (
        LLMConfig,
        Conversation,
        Message,
        RAGCorpus,
        Document,
        DocumentChunk,
        Note,
        NoteChunk,
        ConversationContext,
    )
    
    Base.metadata.create_all(bind=engine)