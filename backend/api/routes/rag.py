"""
API routes for RAG (Retrieval-Augmented Generation) corpus management.
"""

from typing import List, Optional
import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session

from api.deps import get_db_session, get_model_by_id
from api.schemas import (
    RAGCorpusCreate,
    RAGCorpusResponse,
    RAGCorpusDetailResponse,
    RAGCorpusUpdate,
    DocumentResponse,
    UploadDocumentResponse,
)
from db.models import RAGCorpus, Document, DocumentChunk, ConversationContext
from db.utils import paginate

router = APIRouter()


@router.get("/corpus", response_model=List[RAGCorpusResponse])
def list_rag_corpus(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_session)
):
    """
    Get all RAG corpus with pagination.
    """
    pagination = paginate(
        db.query(RAGCorpus),
        page=skip // limit + 1,
        page_size=limit,
        order_by=RAGCorpus.created_at,
        order_direction="desc"
    )
    return pagination["items"]


@router.post("/corpus", response_model=RAGCorpusResponse, status_code=status.HTTP_201_CREATED)
def create_rag_corpus(
    corpus: RAGCorpusCreate,
    db: Session = Depends(get_db_session)
):
    """
    Create a new RAG corpus.
    """
    # Check if name already exists
    existing = db.query(RAGCorpus).filter(RAGCorpus.name == corpus.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"RAG corpus with name '{corpus.name}' already exists"
        )
    
    # Create corpus
    db_corpus = RAGCorpus(**corpus.model_dump())
    db.add(db_corpus)
    db.commit()
    db.refresh(db_corpus)
    
    return db_corpus


@router.get("/corpus/{corpus_id}", response_model=RAGCorpusDetailResponse)
def get_rag_corpus(
    corpus_id: int,
    db: Session = Depends(get_db_session)
):
    """
    Get a specific RAG corpus by ID with its documents.
    """
    db_corpus = get_model_by_id(
        db, 
        RAGCorpus, 
        corpus_id,
        "RAG corpus not found"
    )
    
    return db_corpus


@router.put("/corpus/{corpus_id}", response_model=RAGCorpusResponse)
def update_rag_corpus(
    corpus_id: int,
    corpus: RAGCorpusUpdate,
    db: Session = Depends(get_db_session)
):
    """
    Update a RAG corpus.
    """
    db_corpus = get_model_by_id(
        db, 
        RAGCorpus, 
        corpus_id,
        "RAG corpus not found"
    )
    
    # Check if updating name and it already exists
    if corpus.name and corpus.name != db_corpus.name:
        existing = db.query(RAGCorpus).filter(RAGCorpus.name == corpus.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"RAG corpus with name '{corpus.name}' already exists"
            )
    
    # Update fields if provided
    update_data = corpus.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_corpus, key, value)
    
    db.commit()
    db.refresh(db_corpus)
    
    return db_corpus


@router.delete("/corpus/{corpus_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rag_corpus(
    corpus_id: int,
    db: Session = Depends(get_db_session)
):
    """
    Delete a RAG corpus and all associated documents and chunks.
    """
    db_corpus = get_model_by_id(
        db, 
        RAGCorpus, 
        corpus_id,
        "RAG corpus not found"
    )
    
    # Check if corpus is used by any conversation
    context_count = db.query(ConversationContext).filter(
        ConversationContext.context_type == "rag",
        ConversationContext.context_id == corpus_id
    ).count()
    
    if context_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete RAG corpus: it is used by {context_count} conversation(s)"
        )
    
    db.delete(db_corpus)
    db.commit()
    
    return None


@router.get("/corpus/{corpus_id}/documents", response_model=List[DocumentResponse])
def list_documents(
    corpus_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_session)
):
    """
    Get all documents for a RAG corpus with pagination.
    """
    # Ensure corpus exists
    get_model_by_id(
        db, 
        RAGCorpus, 
        corpus_id,
        "RAG corpus not found"
    )
    
    # Query documents
    pagination = paginate(
        db.query(Document).filter(Document.rag_corpus_id == corpus_id),
        page=skip // limit + 1,
        page_size=limit,
        order_by=Document.created_at,
        order_direction="desc"
    )
    
    return pagination["items"]


@router.post("/corpus/{corpus_id}/upload", response_model=UploadDocumentResponse)
async def upload_document(
    corpus_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session)
):
    """
    Upload a document to a RAG corpus.
    
    This endpoint:
    1. Validates the file is a PDF
    2. Saves the file to disk
    3. Creates a document record
    4. Chunking and embedding will be done asynchronously
    """
    # Ensure corpus exists
    db_corpus = get_model_by_id(
        db, 
        RAGCorpus, 
        corpus_id,
        "RAG corpus not found"
    )
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )
    
    # Create uploads directory if it doesn't exist
    uploads_dir = os.path.join("uploads", "rag", str(corpus_id))
    os.makedirs(uploads_dir, exist_ok=True)
    
    # Save file to disk
    file_path = os.path.join(uploads_dir, file.filename)
    
    # Check if file already exists
    if os.path.exists(file_path):
        # Generate unique filename
        base, ext = os.path.splitext(file.filename)
        i = 1
        while os.path.exists(file_path):
            file_path = os.path.join(uploads_dir, f"{base}_{i}{ext}")
            i += 1
    
    # Write file content
    with open(file_path, "wb") as f:
        file_content = await file.read()
        f.write(file_content)
    
    # Create document record
    document = Document(
        rag_corpus_id=corpus_id,
        filename=os.path.basename(file_path),
        file_path=file_path,
        file_type="pdf"
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # TODO: Queue document processing (chunking and embedding)
    # This will be implemented with the RAG service
    
    return UploadDocumentResponse(
        corpus_id=corpus_id,
        document_id=document.id,
        filename=document.filename,
        success=True,
        message="Document uploaded successfully. Processing will begin shortly."
    )


@router.get("/corpus/{corpus_id}/documents/{document_id}", response_model=DocumentResponse)
def get_document(
    corpus_id: int,
    document_id: int,
    db: Session = Depends(get_db_session)
):
    """
    Get a specific document by ID.
    """
    # Ensure corpus exists
    get_model_by_id(
        db, 
        RAGCorpus, 
        corpus_id,
        "RAG corpus not found"
    )
    
    # Get document
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.rag_corpus_id == corpus_id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found in corpus {corpus_id}"
        )
    
    return document


@router.delete("/corpus/{corpus_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    corpus_id: int,
    document_id: int,
    db: Session = Depends(get_db_session)
):
    """
    Delete a document and all its chunks.
    """
    # Ensure corpus exists
    get_model_by_id(
        db, 
        RAGCorpus, 
        corpus_id,
        "RAG corpus not found"
    )
    
    # Get document
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.rag_corpus_id == corpus_id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found in corpus {corpus_id}"
        )
    
    # Delete file from disk if it exists
    if os.path.exists(document.file_path):
        try:
            os.remove(document.file_path)
        except Exception as e:
            # Log error but continue
            print(f"Error deleting file {document.file_path}: {e}")
    
    # Delete document from database (chunks will cascade)
    db.delete(document)
    db.commit()
    
    return None


@router.post("/corpus/{corpus_id}/documents/{document_id}/process", response_model=dict)
def process_document(
    corpus_id: int,
    document_id: int,
    db: Session = Depends(get_db_session)
):
    """
    Manually trigger processing (chunking and embedding) for a document.
    """
    # Ensure corpus exists
    get_model_by_id(
        db, 
        RAGCorpus, 
        corpus_id,
        "RAG corpus not found"
    )
    
    # Get document
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.rag_corpus_id == corpus_id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found in corpus {corpus_id}"
        )
    
    # TODO: Queue document processing (chunking and embedding)
    # This will be implemented with the RAG service
    
    return {
        "success": True,
        "message": "Document processing queued successfully",
        "document_id": document_id
    }


@router.get("/search", response_model=List[dict])
def search_documents(
    query: str = Query(..., min_length=1, description="Search query"),
    corpus_ids: Optional[List[int]] = Query(None, description="List of corpus IDs to search in"),
    limit: int = Query(10, ge=1, le=100, description="Number of results to return"),
    db: Session = Depends(get_db_session)
):
    """
    Search across RAG corpus using semantic search.
    """
    # This is a placeholder implementation
    # In a real implementation, we would use ChromaDB to perform the search
    
    return [
        {
            "corpus_id": 1,
            "corpus_name": "Sample Corpus",
            "document_id": 1,
            "document_name": "sample.pdf",
            "chunk_id": 1,
            "chunk_text": "This is a sample chunk text that would be returned from the search.",
            "similarity_score": 0.95,
        }
    ]