"""
Tests for the LLM service module.
"""

import pytest
import os
from unittest.mock import patch, MagicMock

# Add the parent directory to Python path for imports to work
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from llm import router
from llm.providers.anthropic import AnthropicProvider
from llm.providers.openai import OpenAIProvider
from llm.providers.local import LocalProvider


@pytest.mark.asyncio
async def test_anthropic_provider_initialization():
    """Test initialization of the Anthropic provider."""
    with patch.object(AnthropicProvider, 'initialize') as mock_init:
        provider = AnthropicProvider()
        await provider.initialize()
        assert mock_init.called


@pytest.mark.asyncio
async def test_openai_provider_initialization():
    """Test initialization of the OpenAI provider."""
    with patch.object(OpenAIProvider, 'initialize') as mock_init:
        provider = OpenAIProvider()
        await provider.initialize()
        assert mock_init.called


@pytest.mark.asyncio
async def test_local_provider_initialization():
    """Test initialization of the Local provider."""
    with patch.object(LocalProvider, 'initialize') as mock_init:
        provider = LocalProvider()
        await provider.initialize()
        assert mock_init.called


@pytest.mark.asyncio
async def test_llm_router_initialization():
    """Test initialization of the LLM router."""
    with patch.object(AnthropicProvider, 'initialize'), \
         patch.object(OpenAIProvider, 'initialize'), \
         patch.object(LocalProvider, 'initialize'):
        
        test_router = router
        await test_router.initialize()
        assert test_router.initialized
        assert len(test_router.providers) == 3


@pytest.mark.asyncio
async def test_router_get_provider():
    """Test getting a provider from the router."""
    with patch.object(AnthropicProvider, 'initialize'), \
         patch.object(AnthropicProvider, 'is_available', return_value=True), \
         patch.object(OpenAIProvider, 'initialize'), \
         patch.object(LocalProvider, 'initialize'):
        
        test_router = router
        await test_router.initialize()
        
        provider = await test_router.get_provider("anthropic")
        assert provider is not None
        assert isinstance(provider, AnthropicProvider)


@pytest.mark.asyncio
async def test_router_generate_response():
    """Test generating a response through the router."""
    # Create a mock response
    mock_response = {
        "content": "This is a test response",
        "model": "test-model",
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15
        }
    }
    
    # Create config dict
    config = {
        "provider": "anthropic",
        "model_name": "claude-3-sonnet-20240229",
        "temperature": 0.7,
        "max_tokens": 1024
    }
    
    with patch.object(AnthropicProvider, 'initialize'), \
         patch.object(AnthropicProvider, 'is_available', return_value=True), \
         patch.object(AnthropicProvider, 'generate_response', return_value=mock_response), \
         patch.object(OpenAIProvider, 'initialize'), \
         patch.object(LocalProvider, 'initialize'):
        
        test_router = router
        await test_router.initialize()
        
        response = await test_router.generate_response(
            config=config,
            prompt="Test prompt",
            system_prompt="You are a helpful assistant"
        )
        
        assert response == mock_response
        assert response["content"] == "This is a test response"