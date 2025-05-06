"""
API routes for RAG (Retrieval-Augmented Generation) corpus management.
"""

from typing import List, Optional
import os
import logging

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

from rag.loader import PDFLoader
from rag.file_manager import FileManager
from rag.service import get_rag_service

logger = logging.getLogger(__name__)

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
    3. Creates a document record
    4. Queues document for processing (chunking, embedding, and indexing)
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
        
        # Queue document for processing
        rag_service = get_rag_service(db_session=db)
        task_id = rag_service.queue_document_processing(document.id)
        
        return UploadDocumentResponse(
            corpus_id=corpus_id,
            document_id=document.id,
            filename=document.filename,
            success=True,
            message=f"Document uploaded successfully ({page_count} pages). Processing started (task_id: {task_id})."
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
    force: bool = Query(False, description="Force reprocessing even if already processed"),
    db: Session = Depends(get_db_session)
):
    """
    Manually trigger processing (chunking, embedding, and indexing) for a document.
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
    
    # Check if document already has chunks and force is not set
    if not force:
        chunk_count = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).count()
        
        if chunk_count > 0:
            return {
                "success": True,
                "message": f"Document already processed with {chunk_count} chunks. Use force=true to reprocess.",
                "document_id": document_id,
                "chunk_count": chunk_count
            }
    
    # Queue document for processing
    rag_service = get_rag_service(db_session=db)
    task_id = rag_service.queue_document_processing(document_id)
    
    return {
        "success": True,
        "message": "Document processing queued successfully",
        "document_id": document_id,
        "task_id": task_id
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
    # Build filter dict if corpus_ids are provided
    filter_dict = None
    if corpus_ids:
        # Get document IDs for these RAG corpus IDs
        documents = db.query(Document).filter(
            Document.rag_corpus_id.in_(corpus_ids)
        ).all()
        
        document_ids = [doc.id for doc in documents]
        
        if document_ids:
            filter_dict = {
                "source_type": "document",
                "source_id": document_ids
            }
        else:
            # No documents found in the specified corpora
            return []
    
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
        
        # Get document info if source_type is document
        document_name = None
        corpus_name = None
        if chunk.source_type == "document" and chunk.source_id:
            document = db.query(Document).filter(Document.id == chunk.source_id).first()
            if document:
                document_name = document.filename
                corpus = db.query(RAGCorpus).filter(RAGCorpus.id == document.rag_corpus_id).first()
                if corpus:
                    corpus_name = corpus.name
        
        response.append({
            "corpus_id": corpus.id if corpus else None,
            "corpus_name": corpus_name,
            "document_id": chunk.source_id if chunk.source_type == "document" else None,
            "document_name": document_name,
            "note_id": chunk.source_id if chunk.source_type == "note" else None,
            "chunk_id": chunk.index,
            "chunk_text": chunk.text,
            "similarity_score": score,
        })
    
    return response

@router.get("/process/status/{task_id}", response_model=dict)
def get_processing_status(
    task_id: str,
    db: Session = Depends(get_db_session)
):
    """
    Get the status of a document or note processing task.
    """
    rag_service = get_rag_service(db_session=db)
    status = rag_service.get_processing_status(task_id)
    
    return status

@router.get("/statistics", response_model=dict)
def get_rag_statistics(
    db: Session = Depends(get_db_session)
):
    """
    Get statistics about the RAG system.
    """
    rag_service = get_rag_service(db_session=db)
    stats = rag_service.get_statistics()
    
    return stats