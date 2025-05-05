"""
OpenAI GPT provider implementation.
"""

import os
import logging
from typing import Dict, List, Optional, Any

from openai import AsyncOpenAI, APIError

from ..base import LLMProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """Provider implementation for OpenAI models."""

    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None):
        """
        Initialize the OpenAI provider.

        Args:
            api_key: OpenAI API key (defaults to env var OPENAI_API_KEY)
            api_url: Optional API URL override
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.api_url = api_url
        self.client = None
        self.available_models = []

    async def initialize(self) -> None:
        """Initialize the OpenAI client."""
        if not self.api_key:
            logger.warning("OpenAI API key not set. Provider will be unavailable.")
            return

        try:
            # Initialize OpenAI client with optional API URL
            kwargs = {"api_key": self.api_key}
            if self.api_url:
                kwargs["base_url"] = self.api_url

            self.client = AsyncOpenAI(**kwargs)
            
            # Attempt to fetch available models
            self.available_models = [
                "gpt-4o",
                "gpt-4-turbo",
                "gpt-4",
                "gpt-3.5-turbo",
            ]
            
            logger.info("OpenAI provider initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI provider: {e}")
            self.client = None

    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = 0.7,
        max_tokens: Optional[int] = 1024,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a response using OpenAI models.

        Args:
            prompt: User message
            system_prompt: System instructions
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters for OpenAI
        
        Returns:
            Response dictionary with content, model, and usage information
        """
        if not self.client:
            raise RuntimeError("OpenAI provider not initialized or unavailable")

        try:
            model = kwargs.get("model", "gpt-3.5-turbo")
            
            # Build the messages array
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            # Make the API call
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Format the response
            result = {
                "content": response.choices[0].message.content,
                "model": model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
            return result
            
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error generating response from OpenAI: {e}")
            raise

    async def get_available_models(self) -> List[str]:
        """Get available OpenAI models."""
        return self.available_models

    def is_available(self) -> bool:
        """Check if OpenAI provider is available."""
        return self.client is not None