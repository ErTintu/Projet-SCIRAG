"""
API routes for personal notes.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from api.deps import get_db_session, get_model_by_id
from api.schemas import (
    NoteCreate,
    NoteResponse,
    NoteDetailResponse,
    NoteUpdate,
    NoteChunkResponse,
)
from db.models import Note, NoteChunk, ConversationContext
from db.utils import paginate

router = APIRouter()


@router.get("/", response_model=List[NoteResponse])
def list_notes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_session)
):
    """
    Get all notes with pagination.
    """
    pagination = paginate(
        db.query(Note),
        page=skip // limit + 1,
        page_size=limit,
        order_by=Note.updated_at,
        order_direction="desc"
    )
    return pagination["items"]


@router.post("/", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    note: NoteCreate,
    db: Session = Depends(get_db_session)
):
    """
    Create a new note.
    
    This endpoint:
    1. Creates a note record
    2. Chunking and embedding will be done automatically
    """
    # Create note record
    db_note = Note(**note.model_dump())
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    
    # TODO: Queue note processing (chunking and embedding)
    # This will be implemented with the RAG service
    
    return db_note


@router.get("/{note_id}", response_model=NoteDetailResponse)
def get_note(
    note_id: int,
    db: Session = Depends(get_db_session)
):
    """
    Get a specific note by ID with its chunks.
    """
    db_note = get_model_by_id(
        db, 
        Note, 
        note_id,
        "Note not found"
    )
    
    return db_note


@router.put("/{note_id}", response_model=NoteResponse)
def update_note(
    note_id: int,
    note: NoteUpdate,
    db: Session = Depends(get_db_session)
):
    """
    Update a note.
    
    This will also trigger re-chunking and re-embedding if content is changed.
    """
    db_note = get_model_by_id(
        db, 
        Note, 
        note_id,
        "Note not found"
    )
    
    # Update fields if provided
    update_data = note.model_dump(exclude_unset=True)
    content_changed = "content" in update_data and update_data["content"] != db_note.content
    
    for key, value in update_data.items():
        setattr(db_note, key, value)
    
    db.commit()
    db.refresh(db_note)
    
    # If content changed, delete existing chunks and re-process
    if content_changed:
        # Delete existing chunks
        db.query(NoteChunk).filter(NoteChunk.note_id == note_id).delete()
        db.commit()
        
        # TODO: Queue note processing (chunking and embedding)
        # This will be implemented with the RAG service
    
    return db_note


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: int,
    db: Session = Depends(get_db_session)
):
    """
    Delete a note and all its chunks.
    """
    db_note = get_model_by_id(
        db, 
        Note, 
        note_id,
        "Note not found"
    )
    
    # Check if note is used by any conversation
    context_count = db.query(ConversationContext).filter(
        ConversationContext.context_type == "note",
        ConversationContext.context_id == note_id
    ).count()
    
    if context_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete note: it is used by {context_count} conversation(s)"
        )
    
    db.delete(db_note)
    db.commit()
    
    return None


@router.get("/{note_id}/chunks", response_model=List[NoteChunkResponse])
def list_note_chunks(
    note_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_session)
):
    """
    Get all chunks for a note with pagination.
    """
    # Ensure note exists
    get_model_by_id(
        db, 
        Note, 
        note_id,
        "Note not found"
    )
    
    # Query chunks
    pagination = paginate(
        db.query(NoteChunk).filter(NoteChunk.note_id == note_id),
        page=skip // limit + 1,
        page_size=limit,
        order_by=NoteChunk.chunk_index,
        order_direction="asc"
    )
    
    return pagination["items"]


@router.post("/{note_id}/process", response_model=dict)
def process_note(
    note_id: int,
    db: Session = Depends(get_db_session)
):
    """
    Manually trigger processing (chunking and embedding) for a note.
    """
    # Ensure note exists
    db_note = get_model_by_id(
        db, 
        Note, 
        note_id,
        "Note not found"
    )
    
    # Delete existing chunks
    db.query(NoteChunk).filter(NoteChunk.note_id == note_id).delete()
    db.commit()
    
    # TODO: Queue note processing (chunking and embedding)
    # This will be implemented with the RAG service
    
    return {
        "success": True,
        "message": "Note processing queued successfully",
        "note_id": note_id
    }


@router.get("/search", response_model=List[dict])
def search_notes(
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Number of results to return"),
    db: Session = Depends(get_db_session)
):
    """
    Search across notes using semantic search.
    """
    # This is a placeholder implementation
    # In a real implementation, we would use ChromaDB to perform the search
    
    return [
        {
            "note_id": 1,
            "note_title": "Sample Note",
            "chunk_id": 1,
            "chunk_text": "This is a sample chunk text that would be returned from the search.",
            "similarity_score": 0.95,
        }
    ]