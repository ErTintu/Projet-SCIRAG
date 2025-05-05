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

from rag.service import get_rag_service
from llm import router as llm_router

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
async def send_message(
    conversation_id: int,
    request: SendMessageRequest,
    db: Session = Depends(get_db_session)
):
    """
    Send a message to the LLM and get a response.
    
    This endpoint:
    1. Creates a user message
    2. Updates active RAG/note contexts if provided
    3. Retrieves relevant context using RAG
    4. Calls the LLM service with context
    5. Creates an assistant message with the response
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
        db.refresh(db_conversation)
    elif not db_conversation.llm_config_id:
        # If no LLM config is set, use default or raise error
        default_config = db.query(LLMConfig).first()
        if not default_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No LLM configuration available. Please set a configuration."
            )
        db_conversation.llm_config_id = default_config.id
        db.commit()
        db.refresh(db_conversation)
    
    # Create user message
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=request.content
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    # Update RAG/note contexts if provided
    if request.active_rags is not None:
        # First, deactivate all RAG contexts
        for ctx in db.query(ConversationContext).filter(
            ConversationContext.conversation_id == conversation_id,
            ConversationContext.context_type == "rag"
        ).all():
            ctx.is_active = False
        
        # Then, activate the specified ones
        for rag_id in request.active_rags:
            context = db.query(ConversationContext).filter(
                ConversationContext.conversation_id == conversation_id,
                ConversationContext.context_type == "rag",
                ConversationContext.context_id == rag_id
            ).first()
            
            if context:
                context.is_active = True
            else:
                # Create if doesn't exist
                context = ConversationContext(
                    conversation_id=conversation_id,
                    context_type="rag",
                    context_id=rag_id,
                    is_active=True
                )
                db.add(context)
    
    if request.active_notes is not None:
        # First, deactivate all note contexts
        for ctx in db.query(ConversationContext).filter(
            ConversationContext.conversation_id == conversation_id,
            ConversationContext.context_type == "note"
        ).all():
            ctx.is_active = False
        
        # Then, activate the specified ones
        for note_id in request.active_notes:
            context = db.query(ConversationContext).filter(
                ConversationContext.conversation_id == conversation_id,
                ConversationContext.context_type == "note",
                ConversationContext.context_id == note_id
            ).first()
            
            if context:
                context.is_active = True
            else:
                # Create if doesn't exist
                context = ConversationContext(
                    conversation_id=conversation_id,
                    context_type="note",
                    context_id=note_id,
                    is_active=True
                )
                db.add(context)
    
    db.commit()
    
    # Get relevant context from RAG
    rag_service = get_rag_service(db_session=db)
    context_text, context_sources = rag_service.get_context_for_query(
        query=request.content,
        conversation_id=conversation_id
    )
    
    # Get LLM config
    llm_config = get_model_by_id(
        db, 
        LLMConfig, 
        db_conversation.llm_config_id,
        "LLM configuration not found"
    )
    
    # Build messages for history (last 10 messages)
    history_messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.desc()).limit(10).all()
    history_messages.reverse()  # Oldest first
    
    # Build system prompt with context
    system_prompt = "You are a helpful assistant that answers questions based on the provided context."
    
    if context_text:
        system_prompt += "\n\nContext information:\n" + context_text
    
    try:
        # Call LLM service
        response = await llm_router.generate_response(
            config=llm_config,
            prompt=request.content,
            system_prompt=system_prompt,
            conversation_history=[(msg.role, msg.content) for msg in history_messages]
        )
        
        # Create assistant message
        assistant_message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=response["content"]
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)
        
        return SendMessageResponse(
            user_message=user_message,
            assistant_message=assistant_message,
            sources=context_sources if context_sources else None
        )
        
    except Exception as e:
        # Log and convert exceptions
        import logging
        logging.error(f"Error generating response: {e}")
        
        # Create error response
        error_message = f"Error generating response: {str(e)}"
        assistant_message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=f"I'm sorry, but there was an error generating a response. Technical details: {error_message}"
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)
        
        return SendMessageResponse(
            user_message=user_message,
            assistant_message=assistant_message,
            sources=None
        )

@router.get("/{conversation_id}/available_sources", response_model=dict)
def get_available_sources(
    conversation_id: int,
    db: Session = Depends(get_db_session)
):
    """
    Get available RAG sources (corpus and notes) for a conversation.
    """
    # Ensure conversation exists
    get_model_by_id(
        db, 
        Conversation, 
        conversation_id,
        "Conversation not found"
    )
    
    # Get RAG service
    rag_service = get_rag_service(db_session=db)
    
    # Get available sources
    sources = rag_service.get_available_sources(conversation_id)
    
    return sources


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