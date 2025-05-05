"""
Local LLM provider implementation using LM Studio.
"""

import os
import logging
import json
from typing import Dict, List, Optional, Any

import httpx

from ..base import LLMProvider

logger = logging.getLogger(__name__)


class LocalProvider(LLMProvider):
    """Provider implementation for local models via LM Studio."""

    def __init__(self, api_url: Optional[str] = None):
        """
        Initialize the local provider.

        Args:
            api_url: URL to LM Studio API (defaults to env var LM_STUDIO_URL)
        """
        self.api_url = api_url or os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1")
        self.client = None
        self.available_models = []

    async def initialize(self) -> None:
        """Initialize the local provider."""
        if not self.api_url:
            logger.warning("LM Studio URL not set. Provider will be unavailable.")
            return

        try:
            # Initialize HTTP client
            self.client = httpx.AsyncClient(base_url=self.api_url, timeout=60.0)
            
            # Test connection
            response = await self.client.get("/models")
            if response.status_code == 200:
                # LM Studio can load multiple models, but the models endpoint might
                # not be implemented in all versions
                try:
                    models_data = response.json()
                    self.available_models = [model["id"] for model in models_data.get("data", [])]
                except:
                    # Fallback: Use default model
                    self.available_models = ["local-model"]
                
                logger.info(f"Local LLM provider initialized successfully with {len(self.available_models)} models")
            else:
                raise Exception(f"Failed to connect to LM Studio: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to initialize Local LLM provider: {e}")
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
        Generate a response using local LLM.

        Args:
            prompt: User message
            system_prompt: System instructions
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters for the local model
        
        Returns:
            Response dictionary with content, model, and usage information
        """
        if not self.client:
            raise RuntimeError("Local LLM provider not initialized or unavailable")

        try:
            # Build the payload
            # LM Studio generally follows the OpenAI format
            payload = {
                "model": kwargs.get("model", "local-model"),
                "messages": [],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            # Add system message if provided
            if system_prompt:
                payload["messages"].append({"role": "system", "content": system_prompt})
            
            # Add user message
            payload["messages"].append({"role": "user", "content": prompt})
            
            # Make the API call
            response = await self.client.post("/chat/completions", json=payload)
            
            if response.status_code != 200:
                raise Exception(f"Error from LM Studio: {response.status_code} - {response.text}")
                
            response_data = response.json()
            
            # Format the response
            # LM Studio may not provide token counts in the same format as OpenAI
            usage = response_data.get("usage", {})
            result = {
                "content": response_data["choices"][0]["message"]["content"],
                "model": "local-model",
                "usage": {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0)
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating response from local LLM: {e}")
            raise

    async def get_available_models(self) -> List[str]:
        """Get available local models."""
        return self.available_models

    def is_available(self) -> bool:
        """Check if local provider is available."""
        return self.client is not None