"""
Conversations Page for SCIRAG.
This page allows users to manage conversations and chat with the LLM.
"""

import streamlit as st
from services.api_client import get_api_client
from components.chat_ui import display_chat, display_sources_selector, display_typing_indicator, system_message
from components.model_selector import display_model_selector
from typing import Dict, List, Any, Optional
import time

# Page config
st.set_page_config(
    page_title="Conversations - SCIRAG",
    page_icon="🔁",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Page title
st.title("🔁 Conversations")
st.markdown("Gérez vos conversations et interagissez avec les modèles LLM.")

# Get API client
api_client = get_api_client()

# Check if API is connected
if not api_client.check_health():
    st.error("❌ L'API n'est pas disponible. Assurez-vous que le backend est en cours d'exécution.")
    st.stop()

# Initialize session state for conversations
if "conversations" not in st.session_state:
    st.session_state.conversations = []
if "current_conversation_id" not in st.session_state:
    st.session_state.current_conversation_id = None
if "active_sources" not in st.session_state:
    st.session_state.active_sources = {"rag": [], "note": []}
if "last_message_count" not in st.session_state:
    st.session_state.last_message_count = 0
if "message_sources" not in st.session_state:
    st.session_state.message_sources = {}

# Functions for conversation actions
def load_conversations():
    """Load all conversations from the API."""
    try:
        conversations = api_client.get_conversations(limit=50)
        st.session_state.conversations = conversations
    except Exception as e:
        st.error(f"Erreur lors du chargement des conversations: {str(e)}")
        st.session_state.conversations = []

def create_new_conversation():
    """Create a new conversation."""
    try:
        # Get LLM configs for default selection
        llm_configs = api_client.get_llm_configs()
        default_config_id = llm_configs[0]["id"] if llm_configs else None
        
        # Create new conversation
        new_conversation = api_client.create_conversation(
            title=f"Nouvelle conversation {time.strftime('%d/%m/%Y %H:%M')}",
            llm_config_id=default_config_id
        )
        
        # Update state
        st.session_state.conversations.insert(0, new_conversation)
        st.session_state.current_conversation_id = new_conversation["id"]
        st.session_state.active_sources = {"rag": [], "note": []}
        
        # Rerun to refresh UI
        st.experimental_rerun()
    except Exception as e:
        st.error(f"Erreur lors de la création d'une nouvelle conversation: {str(e)}")

def delete_conversation(conversation_id: int):
    """Delete a conversation."""
    try:
        # Delete from API
        success = api_client.delete_conversation(conversation_id)
        
        if success:
            # Update state
            st.session_state.conversations = [
                c for c in st.session_state.conversations 
                if c["id"] != conversation_id
            ]
            
            # Clear current conversation if it was deleted
            if st.session_state.current_conversation_id == conversation_id:
                st.session_state.current_conversation_id = None
                st.session_state.active_sources = {"rag": [], "note": []}
            
            # Show success message
            st.success(f"Conversation supprimée avec succès.")
            
            # Rerun to refresh UI
            st.experimental_rerun()
        else:
            st.error("Échec de la suppression de la conversation.")
    except Exception as e:
        st.error(f"Erreur lors de la suppression de la conversation: {str(e)}")

def load_conversation(conversation_id: int):
    """Load a specific conversation and its details."""
    try:
        # Get conversation details
        conversation = api_client.get_conversation(conversation_id)
        
        # Get available sources
        available_sources = api_client.get_available_sources(conversation_id)
        
        # Update active sources
        active_rags = []
        active_notes = []
        
        for corpus in available_sources.get("rag_corpus", []):
            if corpus.get("is_active", False):
                active_rags.append(corpus["id"])
        
        for note in available_sources.get("notes", []):
            if note.get("is_active", False):
                active_notes.append(note["id"])
        
        # Update state
        st.session_state.active_sources = {"rag": active_rags, "note": active_notes}
        
        return conversation, available_sources
    except Exception as e:
        st.error(f"Erreur lors du chargement de la conversation: {str(e)}")
        return None, None

def send_message(conversation_id: int, content: str):
    """Send a message to the conversation and get a response."""
    try:
        # Show typing indicator
        with st.spinner("L'assistant réfléchit..."):
            display_typing_indicator()
            
            # Send message to API
            response = api_client.send_message(
                conversation_id=conversation_id,
                content=content,
                active_rags=st.session_state.active_sources["rag"],
                active_notes=st.session_state.active_sources["note"]
            )
            
            # Return response
            return response
    except Exception as e:
        st.error(f"Erreur lors de l'envoi du message: {str(e)}")
        return None

def update_conversation_model(conversation_id: int, llm_config_id: int):
    """Update the LLM model for a conversation."""
    try:
        api_client.update_conversation(
            conversation_id=conversation_id,
            llm_config_id=llm_config_id
        )
        
        # Show success message
        st.success(f"Modèle LLM mis à jour.")
    except Exception as e:
        st.error(f"Erreur lors de la mise à jour du modèle: {str(e)}")

def update_source_activation(conversation_id: int, context_type: str, context_id: int, is_active: bool):
    """Update the activation state of a source for a conversation."""
    try:
        api_client.update_context_activation(
            conversation_id=conversation_id,
            context_type=context_type,
            context_id=context_id,
            is_active=is_active
        )
        
        # Update session state
        if is_active:
            if context_id not in st.session_state.active_sources.get(context_type, []):
                st.session_state.active_sources[context_type].append(context_id)
        else:
            if context_id in st.session_state.active_sources.get(context_type, []):
                st.session_state.active_sources[context_type].remove(context_id)
    except Exception as e:
        st.error(f"Erreur lors de la mise à jour des sources: {str(e)}")

def rename_conversation(conversation_id: int, new_title: str):
    """Rename a conversation."""
    try:
        api_client.update_conversation(
            conversation_id=conversation_id,
            title=new_title
        )
        
        # Update state
        for i, conv in enumerate(st.session_state.conversations):
            if conv["id"] == conversation_id:
                st.session_state.conversations[i]["title"] = new_title
                break
        
        # Show success message
        st.success(f"Conversation renommée.")
    except Exception as e:
        st.error(f"Erreur lors du renommage de la conversation: {str(e)}")

# Load conversations
load_conversations()

# Sidebar - Conversation List
with st.sidebar:
    st.header("Conversations")
    
    # Create new conversation button
    if st.button("➕ Nouvelle conversation", key="new_conversation"):
        create_new_conversation()
    
    # Divider
    st.markdown("---")
    
    # List of conversations
    if not st.session_state.conversations:
        st.info("Aucune conversation. Créez-en une nouvelle pour commencer.")
    else:
        # Input for searching conversations
        search_query = st.text_input("🔍 Rechercher", key="search_conversations")
        
        # Filter conversations by search query
        filtered_conversations = st.session_state.conversations
        if search_query:
            filtered_conversations = [
                c for c in st.session_state.conversations 
                if search_query.lower() in c.get("title", "").lower()
            ]
        
        if not filtered_conversations:
            st.info(f"Aucune conversation ne correspond à '{search_query}'")
        
        # Display conversations
        for conversation in filtered_conversations:
            conversation_id = conversation["id"]
            title = conversation["title"]
            created_at = conversation.get("created_at", "")
            
            # Format created_at
            date_display = ""
            if created_at:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    date_display = dt.strftime("%d/%m/%Y")
                except:
                    pass
            
            # Create columns for conversation item
            col1, col2 = st.columns([4, 1])
            
            with col1:
                # Button for selecting conversation
                if st.button(
                    f"{title}",
                    key=f"conversation_{conversation_id}",
                    help=f"Créée le {date_display}",
                    use_container_width=True
                ):
                    st.session_state.current_conversation_id = conversation_id
                    st.experimental_rerun()
            
            with col2:
                # Button for deleting conversation
                if st.button(
                    "🗑️",
                    key=f"delete_{conversation_id}",
                    help=f"Supprimer cette conversation",
                ):
                    # Ask for confirmation
                    if "confirm_delete" not in st.session_state:
                        st.session_state.confirm_delete = conversation_id
                        st.warning(f"Voulez-vous vraiment supprimer '{title}'?")
                        st.button(
                            "✓ Confirmer",
                            key=f"confirm_{conversation_id}",
                            on_click=lambda: delete_conversation(st.session_state.confirm_delete)
                        )
                        st.button(
                            "✗ Annuler",
                            key=f"cancel_{conversation_id}",
                            on_click=lambda: st.session_state.pop("confirm_delete", None)
                        )
                    elif st.session_state.confirm_delete == conversation_id:
                        delete_conversation(conversation_id)
                    else:
                        st.session_state.confirm_delete = conversation_id
                        st.warning(f"Voulez-vous vraiment supprimer '{title}'?")
                        st.button(
                            "✓ Confirmer",
                            key=f"confirm_{conversation_id}",
                            on_click=lambda: delete_conversation(st.session_state.confirm_delete)
                        )
                        st.button(
                            "✗ Annuler",
                            key=f"cancel_{conversation_id}",
                            on_click=lambda: st.session_state.pop("confirm_delete", None)
                        )
    
    # Divider
    st.markdown("---")
    
    # Info
    st.info("Sélectionnez une conversation dans la liste ou créez-en une nouvelle pour commencer.")

# Main content - Chat interface
if st.session_state.current_conversation_id:
    # Load the conversation
    conversation, available_sources = load_conversation(st.session_state.current_conversation_id)
    
    if conversation:
        # Conversation title and actions
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Editable title
            new_title = st.text_input(
                "Titre de la conversation",
                value=conversation["title"],
                key="conversation_title"
            )
            
            if new_title != conversation["title"]:
                rename_conversation(conversation["id"], new_title)
        
        with col2:
            # Get LLM Configs
            llm_configs = api_client.get_llm_configs()
            
            # LLM model selector
            display_model_selector(
                llm_configs=llm_configs,
                active_config_id=conversation.get("llm_config_id"),
                on_change=lambda config_id: update_conversation_model(conversation["id"], config_id),
                key_prefix=f"conversation_{conversation['id']}"
            )
        
        # Sources selector
        if available_sources:
            display_sources_selector(
                sources=available_sources,
                active_sources=st.session_state.active_sources,
                on_toggle=lambda context_type, context_id, is_active: update_source_activation(
                    conversation["id"], context_type, context_id, is_active
                ),
                key_prefix=f"conversation_{conversation['id']}"
            )
        
        # Divider
        st.markdown("---")
        
        # Extract messages
        messages = conversation.get("messages", [])
        current_message_count = len(messages)

        # Map message IDs to sources using session state
        conversation_id_str = str(conversation["id"])
        if "message_sources" not in st.session_state:
            st.session_state.message_sources = {}
            
        if conversation_id_str in st.session_state.message_sources:
            message_sources = st.session_state.message_sources[conversation_id_str]
        else:
            message_sources = {}

        # Update last message count
        st.session_state.last_message_count = current_message_count
        
        # Handler for sending a message
        def handle_send_message(content: str):
            # Send message to the API
            response = send_message(conversation["id"], content)
            
            # Extract sources from response
            if response and "sources" in response:
                # Initialiser le dictionnaire de sources si nécessaire
                conversation_id_str = str(conversation["id"])
                if "message_sources" not in st.session_state:
                    st.session_state.message_sources = {}
                if conversation_id_str not in st.session_state.message_sources:
                    st.session_state.message_sources[conversation_id_str] = {}
                    
                # Stocker les sources dans la session state
                message_id = str(response["assistant_message"]["id"])
                st.session_state.message_sources[conversation_id_str][message_id] = response["sources"]
                
                # Mettre à jour le dictionnaire local
                message_sources[message_id] = response["sources"]
            
            # Update the conversation
            st.experimental_rerun()
        
        # Display the chat interface
        display_chat(
            messages=messages,
            sources=message_sources,
            on_send=handle_send_message,
            placeholder="Tapez votre message...",
            key_prefix=f"chat_{conversation['id']}"
        )
else:
    # No conversation selected
    st.info("Aucune conversation sélectionnée. Créez-en une nouvelle ou sélectionnez-en une dans la liste.")
    
    # Create a new conversation button
    if st.button("➕ Créer une nouvelle conversation", key="create_conversation_main"):
        create_new_conversation()
    
    # Show some examples
    st.markdown("### Exemples de requêtes")
    
    example_queries = [
        "Explique-moi comment fonctionne le système RAG de SCIRAG.",
        "Quels sont les avantages d'utiliser des notes personnelles dans une conversation?",
        "Comment puis-je intégrer des documents PDF dans mes conversations?",
        "Quels modèles LLM sont supportés par l'application?"
    ]
    
    for query in example_queries:
        if st.button(query, key=f"example_{hash(query)}"):
            # First create a new conversation
            create_new_conversation()
            
            # Then send this query
            st.session_state.example_query = query
            
            # Rerun to show the conversation
            st.experimental_rerun()
    
    # If we have an example query in session state, use it
    if "example_query" in st.session_state and st.session_state.current_conversation_id:
        query = st.session_state.example_query
        # Send the query
        send_message(st.session_state.current_conversation_id, query)
        # Clear the example query
        del st.session_state.example_query
        # Rerun to show the conversation with response
        st.experimental_rerun()