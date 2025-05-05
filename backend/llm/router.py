"""
LLM router for selecting and using different LLM providers.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from sqlalchemy.orm import Session

from .base import LLMProvider
from .providers.anthropic import AnthropicProvider
from .providers.openai import OpenAIProvider
from .providers.local import LocalProvider
from db.models import LLMConfig

logger = logging.getLogger(__name__)


class LLMRouter:
    """Router for selecting and using different LLM providers."""

    def __init__(self):
        """Initialize the LLM router."""
        self.providers: Dict[str, LLMProvider] = {}
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize all available LLM providers."""
        if self.initialized:
            return

        # Initialize providers
        anthropic_provider = AnthropicProvider()
        openai_provider = OpenAIProvider()
        local_provider = LocalProvider()

        # Add to providers dict
        self.providers = {
            "anthropic": anthropic_provider,
            "openai": openai_provider,
            "local": local_provider,
        }

        # Initialize each provider
        for provider_name, provider in self.providers.items():
            try:
                await provider.initialize()
                if provider.is_available():
                    logger.info(f"Provider {provider_name} initialized successfully")
                else:
                    logger.warning(f"Provider {provider_name} is not available")
            except Exception as e:
                logger.error(f"Failed to initialize provider {provider_name}: {e}")

        self.initialized = True

    async def get_provider(self, provider_name: str) -> Optional[LLMProvider]:
        """
        Get a provider by name.

        Args:
            provider_name: Name of the provider (anthropic, openai, local)

        Returns:
            LLM provider instance or None if not available
        """
        if not self.initialized:
            await self.initialize()

        provider = self.providers.get(provider_name)
        if provider and provider.is_available():
            return provider
        
        return None

    async def get_available_providers(self) -> Dict[str, List[str]]:
        """
        Get all available providers and their models.

        Returns:
            Dictionary of provider names and their available models
        """
        if not self.initialized:
            await self.initialize()

        result = {}
        for name, provider in self.providers.items():
            if provider.is_available():
                models = await provider.get_available_models()
                result[name] = models

        return result

    async def generate_response(
        self,
        config: Union[LLMConfig, Dict[str, Any]],
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a response using the specified LLM configuration.

        Args:
            config: LLM configuration (model or db object)
            prompt: User message
            system_prompt: System instructions
            **kwargs: Additional parameters to pass to the provider

        Returns:
            Response from the LLM provider
        """
        if not self.initialized:
            await self.initialize()

        # Extract configuration
        if isinstance(config, dict):
            provider_name = config.get("provider")
            model_name = config.get("model_name")
            temperature = config.get("temperature", 0.7)
            max_tokens = config.get("max_tokens", 1024)
        else:
            provider_name = config.provider
            model_name = config.model_name
            temperature = config.temperature
            max_tokens = config.max_tokens

        # Get the provider
        provider = await self.get_provider(provider_name)
        if not provider:
            available = ", ".join([p for p, prov in self.providers.items() if prov.is_available()])
            raise ValueError(
                f"Provider '{provider_name}' is not available. Available providers: {available}"
            )

        # Generate the response
        return await provider.generate_response(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model_name,
            **kwargs
        )

    async def get_config_from_db(self, db: Session, config_id: int) -> Optional[LLMConfig]:
        """
        Get an LLM configuration from the database.

        Args:
            db: Database session
            config_id: ID of the LLM configuration

        Returns:
            LLM configuration or None if not found
        """
        return db.query(LLMConfig).filter(LLMConfig.id == config_id).first()