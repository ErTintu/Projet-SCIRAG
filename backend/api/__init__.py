"""
API package for SCIRAG.
"""

from fastapi import APIRouter

from .routes import (
    conversations,
    llm,
    rag,
    notes,
)

# Create main API router
api_router = APIRouter()

# Include all route modules
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(llm.router, prefix="/llm", tags=["llm"])
api_router.include_router(rag.router, prefix="/rag", tags=["rag"])
api_router.include_router(notes.router, prefix="/notes", tags=["notes"])