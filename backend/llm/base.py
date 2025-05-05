"""
Base abstract class for LLM service providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider."""
        pass

    @abstractmethod
    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a response from the LLM.

        Args:
            prompt: User message or prompt
            system_prompt: Optional system prompt/instructions
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            Dictionary containing at minimum:
            {
                "content": str,  # The generated text
                "model": str,    # The model used
                "usage": {       # Token usage information
                    "prompt_tokens": int,
                    "completion_tokens": int,
                    "total_tokens": int
                }
            }
        """
        pass

    @abstractmethod
    async def get_available_models(self) -> List[str]:
        """Get list of available models from this provider."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available (API key set, etc.)."""
        pass