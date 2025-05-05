"""
LLM service module for SCIRAG.
"""

from .router import LLMRouter
from .base import LLMProvider
from .providers.anthropic import AnthropicProvider
from .providers.openai import OpenAIProvider
from .providers.local import LocalProvider

# Singleton instance of the LLM router
router = LLMRouter()

__all__ = [
    "router",
    "LLMProvider",
    "AnthropicProvider",
    "OpenAIProvider",
    "LocalProvider",
]