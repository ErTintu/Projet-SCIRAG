"""
Pydantic schemas for API request/response validation.
"""

from .conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    MessageCreate,
    MessageResponse,
    ConversationDetailResponse,
    SendMessageRequest,
    SendMessageResponse,
)

from .llm import (
    LLMConfigCreate,
    LLMConfigResponse,
    LLMConfigUpdate,
)

from .rag import (
    RAGCorpusCreate, 
    RAGCorpusResponse,
    RAGCorpusUpdate,
    DocumentResponse,
    RAGCorpusDetailResponse,
    UploadDocumentResponse,
)

from .note import (
    NoteCreate,
    NoteResponse,
    NoteUpdate,
    NoteDetailResponse,
    NoteChunkResponse,  # Ajout de cette classe manquante
)

__all__ = [
    "ConversationCreate",
    "ConversationResponse",
    "ConversationUpdate",
    "ConversationDetailResponse",
    "MessageCreate",
    "MessageResponse",
    "SendMessageRequest",
    "SendMessageResponse",
    "LLMConfigCreate", 
    "LLMConfigResponse",
    "LLMConfigUpdate",
    "RAGCorpusCreate",
    "RAGCorpusResponse",
    "RAGCorpusUpdate",
    "RAGCorpusDetailResponse",
    "DocumentResponse",
    "UploadDocumentResponse",
    "NoteCreate",
    "NoteResponse",
    "NoteUpdate",
    "NoteDetailResponse",
    "NoteChunkResponse",  # Ajout ici aussi
]