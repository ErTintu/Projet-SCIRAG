"""
SCIRAG Backend Application
Main entry point for the FastAPI application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import logging

from rag.service import get_rag_service
from db.connection import SessionLocal

# Import API router
from api import api_router
from db.connection import init_db
from llm import router as llm_router

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="SCIRAG API",
    description="Backend API for the SCIRAG Conversational System",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Streamlit default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting SCIRAG API...")
    
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    # Initialize LLM service
    logger.info("Initializing LLM service...")
    await llm_router.initialize()
    
    # Initialize RAG service with a temporary database session
    logger.info("Initializing RAG service...")
    db = SessionLocal()
    try:
        # Initialize RAG service with database session
        get_rag_service(db_session=db)
        logger.info("RAG service initialized")
    finally:
        db.close()
    
    logger.info("SCIRAG API started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down SCIRAG API...")
    
    # Get RAG service and close
    rag_service = get_rag_service()
    rag_service.close()
    logger.info("RAG service closed")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to SCIRAG API", 
        "version": "0.1.0",
        "docs": "/docs",
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting SCIRAG API...")
    
    # Initialize LLM service
    logger.info("Initializing LLM service...")
    await llm_router.initialize()