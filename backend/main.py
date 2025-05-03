"""
SCIRAG Backend Application
Main entry point for the FastAPI application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import logging

# Import routers (to be implemented)
# from api.routes import conversations, rag, llm, notes

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

# Include routers (to be implemented)
# app.include_router(conversations.router, prefix="/api/conversations", tags=["conversations"])
# app.include_router(rag.router, prefix="/api/rag", tags=["rag"])
# app.include_router(llm.router, prefix="/api/llm", tags=["llm"])
# app.include_router(notes.router, prefix="/api/notes", tags=["notes"])

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting SCIRAG API...")
    # Initialize database connection
    # Initialize ChromaDB connection
    # Other startup tasks

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down SCIRAG API...")
    # Close database connections
    # Other cleanup tasks

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to SCIRAG API", "version": "0.1.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}