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

from rag.service import get_rag_service


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
    2. Queues the note for processing (chunking and embedding)
    """
    # Create note record
    db_note = Note(**note.model_dump())
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    
    # Queue note for processing
    rag_service = get_rag_service(db_session=db)
    task_id = rag_service.queue_note_processing(db_note.id)
    
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
    
    # If content changed, trigger reprocessing
    if content_changed:
        # Queue note for processing
        rag_service = get_rag_service(db_session=db)
        rag_service.queue_note_processing(db_note.id)
    
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
    force: bool = Query(False, description="Force reprocessing even if already processed"),
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
    
    # Check if note already has chunks and force is not set
    if not force:
        chunk_count = db.query(NoteChunk).filter(
            NoteChunk.note_id == note_id
        ).count()
        
        if chunk_count > 0:
            return {
                "success": True,
                "message": f"Note already processed with {chunk_count} chunks. Use force=true to reprocess.",
                "note_id": note_id,
                "chunk_count": chunk_count
            }
    
    # Queue note for processing
    rag_service = get_rag_service(db_session=db)
    task_id = rag_service.queue_note_processing(note_id)
    
    return {
        "success": True,
        "message": "Note processing queued successfully",
        "note_id": note_id,
        "task_id": task_id
    }


router.get("/search", response_model=List[dict])
def search_notes(
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Number of results to return"),
    db: Session = Depends(get_db_session)
):
    """
    Search across notes using semantic search.
    """
    # Build filter to only search in notes
    filter_dict = {
        "source_type": "note"
    }
    
    # Use RAG service for search
    rag_service = get_rag_service(db_session=db)
    search_results, _ = rag_service.search(
        query=query,
        limit=limit,
        filter_dict=filter_dict
    )
    
    # Convert results to response format
    response = []
    for result in search_results:
        chunk = result.chunk
        score = result.score
        
        # Get note info
        note_title = None
        if chunk.source_id:
            note = db.query(Note).filter(Note.id == chunk.source_id).first()
            if note:
                note_title = note.title
        
        response.append({
            "note_id": chunk.source_id,
            "note_title": note_title,
            "chunk_id": chunk.index,
            "chunk_text": chunk.text,
            "similarity_score": score,
        })
    
    return response