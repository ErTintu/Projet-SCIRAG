"""
API Client for SCIRAG frontend.
This module handles all communication with the backend API.
"""

import requests
import json
import os
import logging
from typing import Dict, List, Any, Optional, Union
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class APIClient:
    """Client for interacting with the SCIRAG API."""
    
    def __init__(self, api_url: Optional[str] = None):
        """Initialize the API client with the API URL."""
        self.api_url = api_url or os.getenv("API_URL", "http://localhost:8000")
        self.headers = {"Content-Type": "application/json"}
        
        # Cache for frequently accessed data
        self._cache = {}
    
    def _get_url(self, endpoint: str) -> str:
        """Construct a full URL for the given endpoint."""
        # Ensure the endpoint starts with a slash
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"
        
        # Ensure the endpoint starts with /api
        if not endpoint.startswith("/api"):
            endpoint = f"/api{endpoint}"
            
        return f"{self.api_url}{endpoint}"
    
    def _clear_cache(self, keys: Optional[List[str]] = None) -> None:
        """Clear specific keys or all keys from the cache."""
        if keys:
            for key in keys:
                if key in self._cache:
                    del self._cache[key]
        else:
            self._cache = {}
    
    def check_health(self) -> bool:
        """Check if the API is healthy."""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response, raising exceptions for error status codes."""
        if response.status_code >= 400:
            try:
                error_data = response.json()
                error_message = error_data.get("detail", "Unknown error")
            except:
                error_message = response.text or f"HTTP Error {response.status_code}"
            
            logger.error(f"API error: {error_message}")
            raise ValueError(f"API error: {error_message}")
        
        try:
            return response.json()
        except:
            return {"success": True}
    
    # Conversation endpoints
    
    def get_conversations(self, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Get a list of conversations."""
        cache_key = f"conversations_{skip}_{limit}"
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        response = requests.get(
            self._get_url("/conversations"),
            params={"skip": skip, "limit": limit}
        )
        result = self._handle_response(response)
        
        # Cache for 10 seconds
        self._cache[cache_key] = result
        return result
    
    def create_conversation(self, title: str, llm_config_id: Optional[int] = None) -> Dict[str, Any]:
        """Create a new conversation."""
        payload = {"title": title}
        if llm_config_id:
            payload["llm_config_id"] = llm_config_id
            
        response = requests.post(
            self._get_url("/conversations"),
            json=payload,
            headers=self.headers
        )
        result = self._handle_response(response)
        
        # Clear conversations cache
        self._clear_cache(["conversations_"])
        return result
    
    def get_conversation(self, conversation_id: int) -> Dict[str, Any]:
        """Get details of a specific conversation with its messages."""
        cache_key = f"conversation_{conversation_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        response = requests.get(self._get_url(f"/conversations/{conversation_id}"))
        result = self._handle_response(response)
        
        # Cache for 2 seconds (short cache for conversation details)
        self._cache[cache_key] = result
        return result
    
    def update_conversation(self, conversation_id: int, 
                           title: Optional[str] = None, 
                           llm_config_id: Optional[int] = None) -> Dict[str, Any]:
        """Update a conversation."""
        payload = {}
        if title:
            payload["title"] = title
        if llm_config_id:
            payload["llm_config_id"] = llm_config_id
            
        response = requests.put(
            self._get_url(f"/conversations/{conversation_id}"),
            json=payload,
            headers=self.headers
        )
        result = self._handle_response(response)
        
        # Clear related cache
        self._clear_cache([f"conversation_{conversation_id}", "conversations_"])
        return result
    
    def delete_conversation(self, conversation_id: int) -> bool:
        """Delete a conversation."""
        response = requests.delete(self._get_url(f"/conversations/{conversation_id}"))
        
        # Clear related cache
        self._clear_cache([f"conversation_{conversation_id}", "conversations_"])
        
        return response.status_code == 204
    
    def send_message(self, conversation_id: int, content: str, 
                    active_rags: Optional[List[int]] = None,
                    active_notes: Optional[List[int]] = None,
                    llm_config_id: Optional[int] = None) -> Dict[str, Any]:
        """Send a message to the conversation and get an assistant response."""
        payload = {"content": content}
        
        if active_rags is not None:
            payload["active_rags"] = active_rags
        if active_notes is not None:
            payload["active_notes"] = active_notes
        if llm_config_id:
            payload["llm_config_id"] = llm_config_id
            
        response = requests.post(
            self._get_url(f"/conversations/{conversation_id}/send"),
            json=payload,
            headers=self.headers
        )
        result = self._handle_response(response)
        
        # Clear conversation cache
        self._clear_cache([f"conversation_{conversation_id}"])
        
        return result
    
    def get_available_sources(self, conversation_id: int) -> Dict[str, Any]:
        """Get available sources (RAG corpus and notes) for a conversation."""
        cache_key = f"available_sources_{conversation_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        response = requests.get(
            self._get_url(f"/conversations/{conversation_id}/available_sources")
        )
        result = self._handle_response(response)
        
        # Cache for 5 seconds
        self._cache[cache_key] = result
        return result
    
    def update_context_activation(self, conversation_id: int, context_type: str, 
                                 context_id: int, is_active: bool) -> Dict[str, Any]:
        """Activate or deactivate a context (RAG or note) for a conversation."""
        response = requests.post(
            self._get_url(f"/conversations/{conversation_id}/context/{context_type}/{context_id}"),
            params={"is_active": is_active}
        )
        result = self._handle_response(response)
        
        # Clear related cache
        self._clear_cache([
            f"conversation_{conversation_id}", 
            f"available_sources_{conversation_id}"
        ])
        
        return result
    
    # LLM Configuration endpoints
    
    def get_llm_configs(self) -> List[Dict[str, Any]]:
        """Get a list of LLM configurations."""
        cache_key = "llm_configs"
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        response = requests.get(self._get_url("/llm/configs"))
        result = self._handle_response(response)
        
        # Cache for 30 seconds
        self._cache[cache_key] = result
        return result
    
    def create_llm_config(self, name: str, provider: str, model_name: str,
                         api_key: Optional[str] = None, api_url: Optional[str] = None,
                         temperature: float = 0.7, max_tokens: int = 1024) -> Dict[str, Any]:
        """Create a new LLM configuration."""
        payload = {
            "name": name,
            "provider": provider,
            "model_name": model_name,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if api_key:
            payload["api_key"] = api_key
        if api_url:
            payload["api_url"] = api_url
            
        response = requests.post(
            self._get_url("/llm/configs"),
            json=payload,
            headers=self.headers
        )
        result = self._handle_response(response)
        
        # Clear LLM configs cache
        self._clear_cache(["llm_configs"])
        
        return result
    
    def get_llm_providers(self) -> List[Dict[str, Any]]:
        """Get available LLM providers."""
        cache_key = "llm_providers"
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        response = requests.get(self._get_url("/llm/providers"))
        result = self._handle_response(response)
        
        # Cache for 1 hour
        self._cache[cache_key] = result
        return result
    
    def test_llm_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test an LLM configuration without saving it."""
        response = requests.post(
            self._get_url("/llm/test"),
            json=config,
            headers=self.headers
        )
        return self._handle_response(response)
    
    # RAG Corpus endpoints
    
    def get_rag_corpus_list(self) -> List[Dict[str, Any]]:
        """Get a list of RAG corpus."""
        cache_key = "rag_corpus_list"
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        response = requests.get(self._get_url("/rag/corpus"))
        result = self._handle_response(response)
        
        # Cache for 10 seconds
        self._cache[cache_key] = result
        return result
    
    def create_rag_corpus(self, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new RAG corpus."""
        payload = {"name": name}
        if description:
            payload["description"] = description
            
        response = requests.post(
            self._get_url("/rag/corpus"),
            json=payload,
            headers=self.headers
        )
        result = self._handle_response(response)
        
        # Clear RAG corpus cache
        self._clear_cache(["rag_corpus_list"])
        
        return result
    
    def get_rag_corpus(self, corpus_id: int) -> Dict[str, Any]:
        """Get details of a specific RAG corpus with its documents."""
        cache_key = f"rag_corpus_{corpus_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        response = requests.get(self._get_url(f"/rag/corpus/{corpus_id}"))
        result = self._handle_response(response)
        
        # Cache for 5 seconds
        self._cache[cache_key] = result
        return result
    
    def upload_document(self, corpus_id: int, file) -> Dict[str, Any]:
        """Upload a document to a RAG corpus."""
        files = {"file": file}
        
        response = requests.post(
            self._get_url(f"/rag/corpus/{corpus_id}/upload"),
            files=files
        )
        result = self._handle_response(response)
        
        # Clear related cache
        self._clear_cache([f"rag_corpus_{corpus_id}", "rag_corpus_list"])
        
        return result
    
    def get_document_preview(self, corpus_id: int, document_id: int, page: int = 1) -> Dict[str, Any]:
        """Preview a specific page of a document."""
        response = requests.get(
            self._get_url(f"/rag/corpus/{corpus_id}/documents/{document_id}/preview"),
            params={"page": page}
        )
        return self._handle_response(response)
    
    def delete_document(self, corpus_id: int, document_id: int) -> bool:
        """Delete a document from a RAG corpus."""
        response = requests.delete(
            self._get_url(f"/rag/corpus/{corpus_id}/documents/{document_id}")
        )
        
        # Clear related cache
        self._clear_cache([f"rag_corpus_{corpus_id}", "rag_corpus_list"])
        
        return response.status_code == 204
    
    def get_rag_statistics(self) -> Dict[str, Any]:
        """Get statistics about the RAG system."""
        cache_key = "rag_statistics"
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        response = requests.get(self._get_url("/rag/statistics"))
        result = self._handle_response(response)
        
        # Cache for 30 seconds
        self._cache[cache_key] = result
        return result
    
    # Notes endpoints
    
    def get_notes(self) -> List[Dict[str, Any]]:
        """Get a list of notes."""
        cache_key = "notes_list"
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        response = requests.get(self._get_url("/notes"))
        result = self._handle_response(response)
        
        # Cache for 10 seconds
        self._cache[cache_key] = result
        return result
    
    def create_note(self, title: str, content: str) -> Dict[str, Any]:
        """Create a new note."""
        payload = {"title": title, "content": content}
            
        response = requests.post(
            self._get_url("/notes"),
            json=payload,
            headers=self.headers
        )
        result = self._handle_response(response)
        
        # Clear notes cache
        self._clear_cache(["notes_list"])
        
        return result
    
    def get_note(self, note_id: int) -> Dict[str, Any]:
        """Get details of a specific note."""
        cache_key = f"note_{note_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        response = requests.get(self._get_url(f"/notes/{note_id}"))
        result = self._handle_response(response)
        
        # Cache for 5 seconds
        self._cache[cache_key] = result
        return result
    
    def update_note(self, note_id: int, title: Optional[str] = None, 
                   content: Optional[str] = None) -> Dict[str, Any]:
        """Update a note."""
        payload = {}
        if title:
            payload["title"] = title
        if content:
            payload["content"] = content
            
        response = requests.put(
            self._get_url(f"/notes/{note_id}"),
            json=payload,
            headers=self.headers
        )
        result = self._handle_response(response)
        
        # Clear related cache
        self._clear_cache([f"note_{note_id}", "notes_list"])
        
        return result
    
    def delete_note(self, note_id: int) -> bool:
        """Delete a note."""
        response = requests.delete(self._get_url(f"/notes/{note_id}"))
        
        # Clear related cache
        self._clear_cache([f"note_{note_id}", "notes_list"])
        
        return response.status_code == 204
    
    def search_notes(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search across notes using semantic search."""
        response = requests.get(
            self._get_url("/notes/search"),
            params={"query": query, "limit": limit}
        )
        return self._handle_response(response)


# Create a singleton instance for use throughout the app
def get_api_client() -> APIClient:
    """Get or create a singleton instance of the API client."""
    if "api_client" not in st.session_state:
        st.session_state.api_client = APIClient()
    return st.session_state.api_client