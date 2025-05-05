"""
Pydantic schemas for LLM configuration API endpoints.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator


class LLMConfigBase(BaseModel):
    """Base schema for LLM configuration data."""
    name: str = Field(..., description="Configuration name")
    provider: str = Field(..., description="LLM provider (openai, anthropic, cohere, local)")
    model_name: str = Field(..., description="Model name")
    api_key: Optional[str] = Field(None, description="API key (not required for local models)")
    api_url: Optional[str] = Field(None, description="API URL (for local models)")
    temperature: float = Field(0.7, description="Temperature parameter", ge=0.0, le=1.0)
    max_tokens: int = Field(1024, description="Maximum response tokens", ge=1)
    
    @validator('provider')
    def validate_provider(cls, v):
        """Validate that provider is one of the allowed values."""
        allowed_providers = ['openai', 'anthropic', 'cohere', 'local']
        if v.lower() not in allowed_providers:
            raise ValueError(f"Provider must be one of: {', '.join(allowed_providers)}")
        return v.lower()


class LLMConfigCreate(LLMConfigBase):
    """Schema for creating a new LLM configuration."""
    pass


class LLMConfigUpdate(BaseModel):
    """Schema for updating an LLM configuration."""
    name: Optional[str] = None
    provider: Optional[str] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    
    @validator('provider')
    def validate_provider(cls, v):
        """Validate that provider is one of the allowed values."""
        if v is None:
            return v
        allowed_providers = ['openai', 'anthropic', 'cohere', 'local']
        if v.lower() not in allowed_providers:
            raise ValueError(f"Provider must be one of: {', '.join(allowed_providers)}")
        return v.lower()
    
    @validator('temperature')
    def validate_temperature(cls, v):
        """Validate temperature range."""
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError("Temperature must be between 0.0 and 1.0")
        return v
    
    @validator('max_tokens')
    def validate_max_tokens(cls, v):
        """Validate max_tokens is positive."""
        if v is not None and v < 1:
            raise ValueError("Max tokens must be at least 1")
        return v


class LLMConfigResponse(LLMConfigBase):
    """Schema for LLM configuration response."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    # Don't include API key in responses
    api_key: Optional[str] = Field(None, exclude=True)
    
    class Config:
        """Pydantic config."""
        from_attributes = True