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
            self.client = httpx.AsyncClient(base_url=self.api_url, timeout=200.0)
            
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
        """
        if not self.client:
            raise RuntimeError("Local LLM provider not initialized or unavailable")

        try:
            # Inclure le contexte RAG s'il est fourni
            context = kwargs.get("context", "")
            if context:
                prompt = f"Contexte pertinent pour répondre à cette question:\n{context}\n\nQuestion: {prompt}"
                logger.info(f"Added context to prompt (total length: {len(prompt)})")
            
            # Build the payload
            payload = {
                "model": kwargs.get("model", "local-model"),
                "messages": [],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            # Adapter pour LM Studio: inclure le system_prompt dans le premier message user
            first_message = prompt
            if system_prompt:
                first_message = f"{system_prompt}\n\n{prompt}"
            
            # Ajouter message utilisateur
            payload["messages"].append({"role": "user", "content": first_message})
            
            # Récupérer l'historique de conversation si disponible
            conversation_history = kwargs.get("conversation_history", [])
            if conversation_history:
                # Ne garder que les messages avec des rôles supportés
                filtered_history = []
                for role, content in conversation_history:
                    if role in ["user", "assistant"]:
                        filtered_history.append({"role": role, "content": content})
                
                # Remplacer par notre premier message
                if filtered_history:
                    payload["messages"] = filtered_history + [{"role": "user", "content": first_message}]
            
            # Log payload for debugging (sensitive info redacted)
            logger.info(f"Sending request to LM Studio with {len(payload['messages'])} messages")
            
            # Make the API call
            response = await self.client.post("/chat/completions", json=payload)
            
            if response.status_code != 200:
                logger.error(f"Error from LM Studio: {response.status_code} - {response.text}")
                return {
                    "content": "Je n'ai pas pu générer une réponse. Service LLM temporairement indisponible.",
                    "model": "local-model",
                    "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                }
                
            response_data = response.json()
            logger.info(f"Received response from LM Studio: {len(response_data.get('choices', [{}])[0].get('message', {}).get('content', ''))} chars")
            
            # Format the response
            result = {
                "content": response_data["choices"][0]["message"]["content"],
                "model": "local-model",
                "usage": {
                    "prompt_tokens": response_data.get("usage", {}).get("prompt_tokens", 0),
                    "completion_tokens": response_data.get("usage", {}).get("completion_tokens", 0),
                    "total_tokens": response_data.get("usage", {}).get("total_tokens", 0)
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating response from local LLM: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Return a fallback response instead of raising
            return {
                "content": "Je n'ai pas pu générer une réponse en raison d'une erreur technique.",
                "model": "local-model",
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }
    async def get_available_models(self) -> List[str]:
        """Get available local models."""
        return self.available_models

    def is_available(self) -> bool:
        """Check if local provider is available."""
        return self.client is not None