"""
API routes for RAG (Retrieval-Augmented Generation) corpus management.
"""

from typing import List, Optional
import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from rag.loader import PDFLoader
from rag.file_manager import FileManager

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

# Initialiser le FileManager
file_manager = FileManager()

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
    2. Saves the file to disk using FileManager
    3. Extracts text from the PDF
    4. Creates a document record
    5. Prepares for chunking and embedding
    """
    # Ensure corpus exists
    db_corpus = get_model_by_id(
        db, 
        RAGCorpus, 
        corpus_id,
        "RAG corpus not found"
    )
    
    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )
    
    try:
        # Save file using FileManager
        file_info = await file_manager.save_upload_file(file, corpus_id)
        
        # Validate PDF
        if not PDFLoader.is_valid_pdf(file_info["file_path"]):
            # If not valid, delete the file and raise error
            file_manager.delete_file(file_info["file_path"])
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or corrupted PDF file"
            )
        
        # Extract basic metadata
        page_count = PDFLoader.count_pages(file_info["file_path"])
        
        # Create document record
        document = Document(
            rag_corpus_id=corpus_id,
            filename=file_info["filename"],
            file_path=file_info["file_path"],
            file_type=file_info["file_type"]
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
            message=f"Document uploaded successfully ({page_count} pages). Processing will begin shortly."
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log and convert other exceptions
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )

# Route pour prévisualiser un document
@router.get("/corpus/{corpus_id}/documents/{document_id}/preview")
def preview_document(
    corpus_id: int,
    document_id: int,
    page: int = Query(1, ge=1, description="Page number to preview"),
    db: Session = Depends(get_db_session)
):
    """
    Preview the text content of a specific page in a document.
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
    
    try:
        # Validate file exists
        if not os.path.exists(document.file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document file not found: {document.filename}"
            )
            
        # Extract text from the specific page
        pages = PDFLoader.extract_text_by_pages(document.file_path)
        
        # Check if page exists
        if page > len(pages):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Page {page} not found. Document has {len(pages)} pages."
            )
            
        # Return preview data
        return {
            "document_id": document_id,
            "filename": document.filename,
            "total_pages": len(pages),
            "current_page": page,
            "page_content": pages[page-1] if page <= len(pages) else "",
            "has_previous": page > 1,
            "has_next": page < len(pages)
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log and convert other exceptions
        logger.error(f"Error previewing document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preview document: {str(e)}"
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


# Fonction delete_document :
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
    
    # Delete file from disk using FileManager
    if os.path.exists(document.file_path):
        file_manager.delete_file(document.file_path)
    
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