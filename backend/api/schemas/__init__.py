"""
Pydantic schemas for API request/response validation.
"""

from .conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    MessageCreate,
    MessageResponse,
    ConversationDetailResponse,  # Ajout de cette classe manquante
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
    RAGCorpusDetailResponse,  # Ajout de cette classe manquante
)

from .note import (
    NoteCreate,
    NoteResponse,
    NoteUpdate,
    NoteDetailResponse,  # Ajout de cette classe manquante
)

__all__ = [
    "ConversationCreate",
    "ConversationResponse",
    "ConversationUpdate",
    "ConversationDetailResponse",  # Ajout ici aussi
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
    "RAGCorpusDetailResponse",  # Ajout ici aussi
    "DocumentResponse",
    "NoteCreate",
    "NoteResponse",
    "NoteUpdate",
    "NoteDetailResponse",  # Ajout ici aussi
]