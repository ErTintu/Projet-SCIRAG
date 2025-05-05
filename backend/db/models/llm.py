"""
LLM configuration model for SCIRAG.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from ..connection import Base


class LLMConfig(Base):
    """Model for LLM configurations."""
    
    __tablename__ = "llm_configs"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    provider = Column(
        String(50),
        nullable=False,
        comment="Provider type: openai, anthropic, cohere, local"
    )
    model_name = Column(String(255), nullable=False)
    api_key = Column(Text, nullable=True)
    api_url = Column(Text, nullable=True)
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=1024)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<LLMConfig(name='{self.name}', provider='{self.provider}', model='{self.model_name}')>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider,
            "model_name": self.model_name,
            "api_url": self.api_url,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }