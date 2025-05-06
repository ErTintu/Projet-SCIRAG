"""
Pydantic schemas for note-related API endpoints.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class NoteBase(BaseModel):
    """Base schema for note data."""
    title: str = Field(..., description="Note title")
    content: str = Field(..., description="Note content")


class NoteCreate(NoteBase):
    """Schema for creating a new note."""
    pass


class NoteUpdate(BaseModel):
    """Schema for updating a note."""
    title: Optional[str] = Field(None, description="New note title")
    content: Optional[str] = Field(None, description="New note content")


class NoteChunkBase(BaseModel):
    """Base schema for note chunk data."""
    chunk_text: str = Field(..., description="Text content of the chunk")
    chunk_index: int = Field(..., description="Index position of the chunk")


class NoteChunkCreate(NoteChunkBase):
    """Schema for creating a new note chunk."""
    note_id: int = Field(..., description="ID of the parent note")


class NoteChunkResponse(NoteChunkBase):
    """Schema for note chunk response."""
    id: int
    note_id: int
    created_at: datetime
    has_embedding: bool = Field(True, description="Whether the chunk has an embedding")
   
    class Config:
        """Pydantic config."""
        from_attributes = True


class NoteResponse(NoteBase):
    """Schema for note response."""
    id: int
    created_at: datetime
    updated_at: datetime
    chunk_count: int = Field(0, description="Number of chunks in the note")
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class NoteDetailResponse(NoteResponse):
    """Schema for detailed note response including chunks."""
    chunks: List[NoteChunkResponse] = []
    
    class Config:
        """Pydantic config."""
        from_attributes = True