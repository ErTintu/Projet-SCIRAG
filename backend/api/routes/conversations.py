"""
API routes for conversations.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from api.deps import get_db_session, get_model_by_id
from api.schemas import (
    ConversationCreate,
    ConversationResponse,
    ConversationDetailResponse,
    ConversationUpdate,
    MessageCreate,
    MessageResponse,
    SendMessageRequest,
    SendMessageResponse,
)
from db.models import Conversation, Message, LLMConfig, ConversationContext
from db.utils import paginate

router = APIRouter()


@router.get("/", response_model=List[ConversationResponse])
def list_conversations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_session)
):
    """
    Get all conversations with pagination.
    """
    pagination = paginate(
        db.query(Conversation),
        page=skip // limit + 1,
        page_size=limit,
        order_by=Conversation.updated_at,
        order_direction="desc"
    )
    return pagination["items"]


@router.post("/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    conversation: ConversationCreate,
    db: Session = Depends(get_db_session)
):
    """
    Create a new conversation.
    """
    # Validate LLM config if provided
    if conversation.llm_config_id:
        get_model_by_id(
            db, 
            LLMConfig, 
            conversation.llm_config_id,
            "LLM configuration not found"
        )
    
    # Create conversation
    db_conversation = Conversation(**conversation.model_dump())
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    
    return db_conversation


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db_session)
):
    """
    Get a specific conversation by ID with its messages.
    """
    db_conversation = get_model_by_id(
        db, 
        Conversation, 
        conversation_id,
        "Conversation not found"
    )
    
    return db_conversation


@router.put("/{conversation_id}", response_model=ConversationResponse)
def update_conversation(
    conversation_id: int,
    conversation: ConversationUpdate,
    db: Session = Depends(get_db_session)
):
    """
    Update a conversation.
    """
    db_conversation = get_model_by_id(
        db, 
        Conversation, 
        conversation_id,
        "Conversation not found"
    )
    
    # Validate LLM config if provided
    if conversation.llm_config_id:
        get_model_by_id(
            db, 
            LLMConfig, 
            conversation.llm_config_id,
            "LLM configuration not found"
        )
    
    # Update fields if provided
    update_data = conversation.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_conversation, key, value)
    
    db.commit()
    db.refresh(db_conversation)
    
    return db_conversation


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db_session)
):
    """
    Delete a conversation.
    """
    db_conversation = get_model_by_id(
        db, 
        Conversation, 
        conversation_id,
        "Conversation not found"
    )
    
    db.delete(db_conversation)
    db.commit()
    
    return None


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
def list_messages(
    conversation_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_session)
):
    """
    Get all messages for a conversation with pagination.
    """
    # Ensure conversation exists
    get_model_by_id(
        db, 
        Conversation, 
        conversation_id,
        "Conversation not found"
    )
    
    # Query messages
    pagination = paginate(
        db.query(Message).filter(Message.conversation_id == conversation_id),
        page=skip // limit + 1,
        page_size=limit,
        order_by=Message.created_at,
        order_direction="asc"
    )
    
    return pagination["items"]


@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_message(
    conversation_id: int,
    message: MessageCreate,
    db: Session = Depends(get_db_session)
):
    """
    Create a new message in a conversation.
    """
    # Ensure conversation exists
    get_model_by_id(
        db, 
        Conversation, 
        conversation_id,
        "Conversation not found"
    )
    
    # Create message
    db_message = Message(
        conversation_id=conversation_id,
        role=message.role,
        content=message.content
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    return db_message


@router.post("/{conversation_id}/send", response_model=SendMessageResponse)
def send_message(
    conversation_id: int,
    request: SendMessageRequest,
    db: Session = Depends(get_db_session)
):
    """
    Send a message to the LLM and get a response.
    
    This endpoint:
    1. Creates a user message
    2. Updates active RAG/note contexts if provided
    3. Calls the LLM service with context
    4. Creates an assistant message with the response
    """
    # Ensure conversation exists
    db_conversation = get_model_by_id(
        db, 
        Conversation, 
        conversation_id,
        "Conversation not found"
    )
    
    # If LLM config ID is provided, update the conversation
    if request.llm_config_id:
        llm_config = get_model_by_id(
            db, 
            LLMConfig, 
            request.llm_config_id,
            "LLM configuration not found"
        )
        db_conversation.llm_config_id = llm_config.id
        db.commit()
    
    # Create user message
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=request.content
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    # TODO: Update RAG/note contexts if provided
    # This will be implemented with the RAG service
    
    # TODO: Call LLM service with context
    # This will be implemented with the LLM service
    # For now, just create a dummy response
    
    # Create assistant message (placeholder)
    assistant_message = Message(
        conversation_id=conversation_id,
        role="assistant",
        content="This is a placeholder response. LLM service integration will be implemented in a future PR."
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)
    
    return SendMessageResponse(
        user_message=user_message,
        assistant_message=assistant_message,
        sources=None  # Will be populated when RAG is implemented
    )


@router.get("/{conversation_id}/context", response_model=List[dict])
def get_conversation_context(
    conversation_id: int,
    context_type: Optional[str] = Query(None, description="Filter by context type (rag or note)"),
    active_only: bool = Query(True, description="Filter by active status"),
    db: Session = Depends(get_db_session)
):
    """
    Get all context items for a conversation.
    """
    # Ensure conversation exists
    get_model_by_id(
        db, 
        Conversation, 
        conversation_id,
        "Conversation not found"
    )
    
    # Build query
    query = db.query(ConversationContext).filter(
        ConversationContext.conversation_id == conversation_id
    )
    
    # Apply filters
    if context_type:
        query = query.filter(ConversationContext.context_type == context_type)
    
    if active_only:
        query = query.filter(ConversationContext.is_active == True)
    
    context_items = query.all()
    
    # Convert to dict for easier consumption in frontend
    return [item.to_dict() for item in context_items]


@router.post("/{conversation_id}/context/{context_type}/{context_id}", status_code=status.HTTP_200_OK)
def update_context_activation(
    conversation_id: int,
    context_type: str,
    context_id: int,
    is_active: bool = Query(True, description="Whether the context should be active"),
    db: Session = Depends(get_db_session)
):
    """
    Activate or deactivate a context item for a conversation.
    """
    # Ensure conversation exists
    get_model_by_id(
        db, 
        Conversation, 
        conversation_id,
        "Conversation not found"
    )
    
    # Validate context_type
    if context_type not in ["rag", "note"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Context type must be 'rag' or 'note'"
        )
    
    # Find or create context item
    db_context = db.query(ConversationContext).filter(
        ConversationContext.conversation_id == conversation_id,
        ConversationContext.context_type == context_type,
        ConversationContext.context_id == context_id
    ).first()
    
    if db_context:
        # Update existing context
        db_context.is_active = is_active
    else:
        # Create new context
        db_context = ConversationContext(
            conversation_id=conversation_id,
            context_type=context_type,
            context_id=context_id,
            is_active=is_active
        )
        db.add(db_context)
    
    db.commit()
    
    return {"status": "success", "is_active": is_active}