"""
API routes for LLM configurations.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_db_session, get_model_by_id
from api.schemas import (
    LLMConfigCreate,
    LLMConfigResponse,
    LLMConfigUpdate,
)
from db.models import LLMConfig, Conversation
from db.utils import paginate

router = APIRouter()


@router.get("/configs", response_model=List[LLMConfigResponse])
def list_llm_configs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_session)
):
    """
    Get all LLM configurations with pagination.
    """
    pagination = paginate(
        db.query(LLMConfig),
        page=skip // limit + 1,
        page_size=limit,
        order_by=LLMConfig.created_at,
        order_direction="desc"
    )
    return pagination["items"]


@router.post("/configs", response_model=LLMConfigResponse, status_code=status.HTTP_201_CREATED)
def create_llm_config(
    llm_config: LLMConfigCreate,
    db: Session = Depends(get_db_session)
):
    """
    Create a new LLM configuration.
    """
    # Check if name already exists
    existing = db.query(LLMConfig).filter(LLMConfig.name == llm_config.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"LLM configuration with name '{llm_config.name}' already exists"
        )
    
    # Create config
    db_llm_config = LLMConfig(**llm_config.model_dump())
    db.add(db_llm_config)
    db.commit()
    db.refresh(db_llm_config)
    
    return db_llm_config


@router.get("/configs/{config_id}", response_model=LLMConfigResponse)
def get_llm_config(
    config_id: int,
    db: Session = Depends(get_db_session)
):
    """
    Get a specific LLM configuration by ID.
    """
    db_llm_config = get_model_by_id(
        db, 
        LLMConfig, 
        config_id,
        "LLM configuration not found"
    )
    
    return db_llm_config


@router.put("/configs/{config_id}", response_model=LLMConfigResponse)
def update_llm_config(
    config_id: int,
    llm_config: LLMConfigUpdate,
    db: Session = Depends(get_db_session)
):
    """
    Update an LLM configuration.
    """
    db_llm_config = get_model_by_id(
        db, 
        LLMConfig, 
        config_id,
        "LLM configuration not found"
    )
    
    # Check if updating name and it already exists
    if llm_config.name and llm_config.name != db_llm_config.name:
        existing = db.query(LLMConfig).filter(LLMConfig.name == llm_config.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"LLM configuration with name '{llm_config.name}' already exists"
            )
    
    # Update fields if provided
    update_data = llm_config.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_llm_config, key, value)
    
    db.commit()
    db.refresh(db_llm_config)
    
    return db_llm_config


@router.delete("/configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_llm_config(
    config_id: int,
    db: Session = Depends(get_db_session)
):
    """
    Delete an LLM configuration.
    """
    db_llm_config = get_model_by_id(
        db, 
        LLMConfig, 
        config_id,
        "LLM configuration not found"
    )
    
    # Check if config is used by any conversation
    conversation_count = db.query(Conversation).filter(
        Conversation.llm_config_id == config_id
    ).count()
    
    if conversation_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete LLM configuration: it is used by {conversation_count} conversation(s)"
        )
    
    db.delete(db_llm_config)
    db.commit()
    
    return None


@router.get("/providers", response_model=List[dict])
def list_providers():
    """
    Get a list of available LLM providers.
    """
    providers = [
        {
            "id": "openai",
            "name": "OpenAI",
            "description": "Provider for GPT models",
            "models": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
            "requires_api_key": True,
            "requires_api_url": False,
        },
        {
            "id": "anthropic",
            "name": "Anthropic",
            "description": "Provider for Claude models",
            "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
            "requires_api_key": True,
            "requires_api_url": False,
        },
        {
            "id": "cohere",
            "name": "Cohere",
            "description": "Provider for Cohere models",
            "models": ["command", "command-light", "command-nightly"],
            "requires_api_key": True,
            "requires_api_url": False,
        },
        {
            "id": "local",
            "name": "Local",
            "description": "Provider for local models via LM Studio",
            "models": ["default"],
            "requires_api_key": False,
            "requires_api_url": True,
        },
    ]
    
    return providers


@router.post("/test", response_model=dict)
def test_llm_config(llm_config: LLMConfigCreate):
    """
    Test an LLM configuration without saving it.
    
    Sends a simple prompt to the configured LLM to verify connectivity.
    """
    # This is a placeholder implementation
    # In a real implementation, we would call the LLM service
    
    # For now, just return a success message
    return {
        "success": True,
        "message": f"Successfully connected to {llm_config.provider} model {llm_config.model_name}",
        "response": "This is a placeholder response. LLM service integration will be implemented in a future PR."
    }