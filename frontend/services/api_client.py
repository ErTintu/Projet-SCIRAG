import requests
import os
import logging
from typing import Dict, List, Optional, Any, Union

class APIClient:
    """Client pour l'API SCIRAG."""
    
    def __init__(self, base_url: str):
        """Initialise le client API avec l'URL de base."""
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)
    
    def check_health(self) -> bool:
        """Vérifie la disponibilité de l'API."""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification de l'API: {e}")
            return False
    
    # Méthodes pour les conversations
    def list_conversations(self) -> List[Dict]:
        """Récupère la liste des conversations."""
        try:
            response = self.session.get(f"{self.base_url}/api/conversations")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des conversations: {e}")
            return []
    
    def create_conversation(self, title: str, llm_config_id: Optional[int] = None) -> Dict:
        """Crée une nouvelle conversation."""
        data = {"title": title}
        if llm_config_id:
            data["llm_config_id"] = llm_config_id
        
        response = self.session.post(
            f"{self.base_url}/api/conversations",
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def get_conversation(self, conversation_id: int) -> Dict:
        """Récupère les détails d'une conversation."""
        response = self.session.get(
            f"{self.base_url}/api/conversations/{conversation_id}"
        )
        response.raise_for_status()
        return response.json()
    
    def delete_conversation(self, conversation_id: int) -> bool:
        """Supprime une conversation."""
        try:
            response = self.session.delete(
                f"{self.base_url}/api/conversations/{conversation_id}"
            )
            response.raise_for_status()
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de la suppression de la conversation {conversation_id}: {e}")
            return False
    
    def send_message(
        self, 
        conversation_id: int, 
        content: str,
        llm_config_id: Optional[int] = None,
        active_rags: Optional[List[int]] = None,
        active_notes: Optional[List[int]] = None
    ) -> Dict:
        """Envoie un message et obtient une réponse."""
        data = {
            "content": content
        }
        
        if llm_config_id:
            data["llm_config_id"] = llm_config_id
        
        if active_rags is not None:
            data["active_rags"] = active_rags
        
        if active_notes is not None:
            data["active_notes"] = active_notes
        
        response = self.session.post(
            f"{self.base_url}/api/conversations/{conversation_id}/send",
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def get_available_sources(self, conversation_id: int) -> Dict:
        """Récupère les sources disponibles pour une conversation."""
        response = self.session.get(
            f"{self.base_url}/api/conversations/{conversation_id}/available_sources"
        )
        response.raise_for_status()
        return response.json()
    
    def update_context_activation(
        self, 
        conversation_id: int, 
        context_type: str, 
        context_id: int, 
        is_active: bool
    ) -> Dict:
        """Active ou désactive un contexte pour une conversation."""
        response = self.session.post(
            f"{self.base_url}/api/conversations/{conversation_id}/context/{context_type}/{context_id}?is_active={str(is_active).lower()}"
        )
        response.raise_for_status()
        return response.json()
    
    # Méthodes pour les RAG corpus
    def list_rag_corpus(self) -> List[Dict]:
        """Récupère la liste des corpus RAG."""
        try:
            response = self.session.get(f"{self.base_url}/api/rag/corpus")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des corpus RAG: {e}")
            return []
    
    def create_rag_corpus(self, name: str, description: Optional[str] = None) -> Dict:
        """Crée un nouveau corpus RAG."""
        data = {
            "name": name,
            "description": description
        }
        
        response = self.session.post(
            f"{self.base_url}/api/rag/corpus",
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def get_rag_corpus(self, corpus_id: int) -> Dict:
        """Récupère les détails d'un corpus RAG."""
        response = self.session.get(
            f"{self.base_url}/api/rag/corpus/{corpus_id}"
        )
        response.raise_for_status()
        return response.json()
    
    def upload_document(self, corpus_id: int, file_path: str) -> Dict:
        """Upload un document dans un corpus RAG."""
        with open(file_path, "rb") as f:
            file_data = f.read()
        
        files = {
            "file": (os.path.basename(file_path), file_data, "application/pdf")
        }
        
        response = self.session.post(
            f"{self.base_url}/api/rag/corpus/{corpus_id}/upload",
            files=files
        )
        response.raise_for_status()
        return response.json()
    
    def delete_document(self, corpus_id: int, document_id: int) -> bool:
        """Supprime un document d'un corpus RAG."""
        try:
            response = self.session.delete(
                f"{self.base_url}/api/rag/corpus/{corpus_id}/documents/{document_id}"
            )
            response.raise_for_status()
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de la suppression du document {document_id}: {e}")
            return False
    
    # Méthodes pour les notes
    def list_notes(self) -> List[Dict]:
        """Récupère la liste des notes."""
        try:
            response = self.session.get(f"{self.base_url}/api/notes")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des notes: {e}")
            return []
    
    def create_note(self, title: str, content: str) -> Dict:
        """Crée une nouvelle note."""
        data = {
            "title": title,
            "content": content
        }
        
        response = self.session.post(
            f"{self.base_url}/api/notes",
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def get_note(self, note_id: int) -> Dict:
        """Récupère les détails d'une note."""
        response = self.session.get(
            f"{self.base_url}/api/notes/{note_id}"
        )
        response.raise_for_status()
        return response.json()
    
    def update_note(self, note_id: int, title: Optional[str] = None, content: Optional[str] = None) -> Dict:
        """Met à jour une note existante."""
        data = {}
        if title is not None:
            data["title"] = title
        if content is not None:
            data["content"] = content
        
        response = self.session.put(
            f"{self.base_url}/api/notes/{note_id}",
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def delete_note(self, note_id: int) -> bool:
        """Supprime une note."""
        try:
            response = self.session.delete(
                f"{self.base_url}/api/notes/{note_id}"
            )
            response.raise_for_status()
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de la suppression de la note {note_id}: {e}")
            return False
    
    # Méthodes pour les configurations LLM
    def list_llm_configs(self) -> List[Dict]:
        """Récupère la liste des configurations LLM."""
        try:
            response = self.session.get(f"{self.base_url}/api/llm/configs")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des configurations LLM: {e}")
            return []
    
    def list_llm_providers(self) -> List[Dict]:
        """Récupère la liste des fournisseurs LLM disponibles."""
        try:
            response = self.session.get(f"{self.base_url}/api/llm/providers")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des providers LLM: {e}")
            return []
    
    def create_llm_config(
        self, 
        name: str, 
        provider: str, 
        model_name: str,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> Dict:
        """Crée une nouvelle configuration LLM."""
        data = {
            "name": name,
            "provider": provider,
            "model_name": model_name,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if api_key:
            data["api_key"] = api_key
        
        if api_url:
            data["api_url"] = api_url
        
        response = self.session.post(
            f"{self.base_url}/api/llm/configs",
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def get_llm_config(self, config_id: int) -> Dict:
        """Récupère les détails d'une configuration LLM."""
        response = self.session.get(
            f"{self.base_url}/api/llm/configs/{config_id}"
        )
        response.raise_for_status()
        return response.json()