"""
Pydantic schemas for conversation-related API endpoints.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class MessageBase(BaseModel):
    """Base schema for message data."""
    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")


class MessageCreate(MessageBase):
    """Schema for creating a new message."""
    conversation_id: int


class MessageResponse(MessageBase):
    """Schema for message response."""
    id: int
    conversation_id: int
    created_at: datetime
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class ConversationBase(BaseModel):
    """Base schema for conversation data."""
    title: str = Field(..., description="Conversation title")


class ConversationCreate(ConversationBase):
    """Schema for creating a new conversation."""
    llm_config_id: Optional[int] = Field(None, description="ID of the LLM configuration to use")


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation."""
    title: Optional[str] = Field(None, description="New conversation title")
    llm_config_id: Optional[int] = Field(None, description="New LLM configuration ID")


class ConversationResponse(ConversationBase):
    """Schema for conversation response."""
    id: int
    llm_config_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class ConversationDetailResponse(ConversationResponse):
    """Schema for detailed conversation response including messages."""
    messages: List[MessageResponse] = []
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class ContextItemBase(BaseModel):
    """Base schema for conversation context items (RAG/notes)."""
    context_type: str = Field(..., description="Type of context (rag, note)")
    context_id: int = Field(..., description="ID of the context item")
    is_active: bool = Field(True, description="Whether the context item is active")


class ContextItemCreate(ContextItemBase):
    """Schema for creating a new context item."""
    conversation_id: int


class ContextItemResponse(ContextItemBase):
    """Schema for context item response."""
    id: int
    conversation_id: int
    created_at: datetime
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class SendMessageRequest(BaseModel):
    """Schema for sending a message to the assistant."""
    content: str = Field(..., description="Message content")
    active_rags: Optional[List[int]] = Field(None, description="List of active RAG corpus IDs")
    active_notes: Optional[List[int]] = Field(None, description="List of active note IDs")
    llm_config_id: Optional[int] = Field(None, description="LLM configuration ID to use")


class SendMessageResponse(BaseModel):
    """Schema for the response from sending a message."""
    user_message: MessageResponse
    assistant_message: MessageResponse
    sources: Optional[List[Dict[str, Any]]] = Field(None, description="Sources used in the response")