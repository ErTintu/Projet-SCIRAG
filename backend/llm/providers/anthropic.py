"""
Anthropic Claude LLM provider implementation.
"""

import os
import logging
from typing import Dict, List, Optional, Any

import anthropic
from anthropic.types import MessageParam

from ..base import LLMProvider

logger = logging.getLogger(__name__)


class AnthropicProvider(LLMProvider):
    """Provider implementation for Anthropic Claude models."""

    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None):
        """
        Initialize the Anthropic provider.

        Args:
            api_key: Anthropic API key (defaults to env var ANTHROPIC_API_KEY)
            api_url: Optional API URL override
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.api_url = api_url
        self.client = None
        self.available_models = []

    async def initialize(self) -> None:
        """Initialize the Anthropic client."""
        if not self.api_key:
            logger.warning("Anthropic API key not set. Provider will be unavailable.")
            return

        try:
            # Initialize Anthropic client with optional API URL
            kwargs = {"api_key": self.api_key}
            if self.api_url:
                kwargs["base_url"] = self.api_url

            self.client = anthropic.Anthropic(**kwargs)
            
            # Claude models available as of the time of development
            self.available_models = [
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229", 
                "claude-3-haiku-20240307",
                "claude-2.1",
                "claude-2.0",
                "claude-instant-1.2"
            ]
            
            logger.info("Anthropic Claude provider initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic provider: {e}")
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
        Generate a response using Claude.

        Args:
            prompt: User message
            system_prompt: System instructions
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters for Claude
        
        Returns:
            Response dictionary with content, model, and usage information
        """
        if not self.client:
            raise RuntimeError("Anthropic provider not initialized or unavailable")

        try:
            model = kwargs.get("model", "claude-3-sonnet-20240229")
            
            # Prepare the messages array
            messages: List[MessageParam] = [
                {"role": "user", "content": prompt}
            ]
            
            # Make the API call
            response = self.client.messages.create(
                model=model,
                messages=messages,
                system=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Format the response
            result = {
                "content": response.content[0].text,
                "model": model,
                "usage": {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating response from Claude: {e}")
            raise

    async def get_available_models(self) -> List[str]:
        """Get available Claude models."""
        return self.available_models

    def is_available(self) -> bool:
        """Check if Claude provider is available."""
        return self.client is not None