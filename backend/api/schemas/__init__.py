"""
Pydantic schemas for API request/response validation.
"""

from .conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    MessageCreate,
    MessageResponse,
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
)

from .note import (
    NoteCreate,
    NoteResponse,
    NoteUpdate,
)

__all__ = [
    "ConversationCreate",
    "ConversationResponse",
    "ConversationUpdate",
    "MessageCreate",
    "MessageResponse",
    "LLMConfigCreate", 
    "LLMConfigResponse",
    "LLMConfigUpdate",
    "RAGCorpusCreate",
    "RAGCorpusResponse",
    "RAGCorpusUpdate",
    "DocumentResponse",
    "NoteCreate",
    "NoteResponse",
    "NoteUpdate",
]