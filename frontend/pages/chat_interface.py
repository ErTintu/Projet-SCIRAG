import gradio as gr
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
import time

from components.message_block import render_message
from components.source_viewer import render_sources
from components.model_selector import create_model_selector
from components.context_selector import create_context_selector

logger = logging.getLogger(__name__)

def create_chat_interface(api_client):
    """
    Crée l'interface de conversation.
    
    Args:
        api_client: Instance du client API
        
    Returns:
        Dict contenant les composants de l'interface
    """
    # État de l'application
    conversation_state = gr.State({
        "current_conversation_id": None,
        "conversations": [],
        "messages": [],
        "sources": [],
        "error": None
    })
    
    # État pour stocker l'ID de la conversation courante
    current_conversation_id = gr.State(None)
    
    # Fonction pour charger les conversations
    def load_conversations():
        try:
            conversations = api_client.list_conversations()
            return {
                "conversations": conversations,
                "current_conversation_id": conversations[0]["id"] if conversations else None,
                "error": None
            }, conversations[0]["id"] if conversations else None
        except Exception as e:
            logger.error(f"Erreur lors du chargement des conversations: {e}")
            return {
                "conversations": [],
                "error": str(e)
            }, None
    
    # Fonction pour créer une nouvelle conversation
    def create_new_conversation(title, llm_config_id):
        if not title:
            return {
                "error": "Le titre ne peut pas être vide"
            }, None
        
        try:
            new_conversation = api_client.create_conversation(
                title=title,
                llm_config_id=llm_config_id
            )
            
            conversations = api_client.list_conversations()
            
            return {
                "conversations": conversations,
                "current_conversation_id": new_conversation["id"],
                "messages": [],
                "sources": [],
                "error": None
            }, new_conversation["id"]
        except Exception as e:
            logger.error(f"Erreur lors de la création de la conversation: {e}")
            return {
                "error": str(e)
            }, None
    
    # Fonction pour charger une conversation existante
    def load_conversation(conversation_id):
        if not conversation_id:
            return {
                "current_conversation_id": None,
                "messages": [],
                "sources": [],
                "error": None
            }, None
        
        # Si conversation_id est un tuple (nom, id), extraire l'id
        if isinstance(conversation_id, (list, tuple)) and len(conversation_id) > 1:
            conversation_id = conversation_id[1]
        
        try:
            conversation = api_client.get_conversation(conversation_id)
            
            return {
                "current_conversation_id": conversation_id,
                "messages": conversation.get("messages", []),
                "sources": [],  # Réinitialiser les sources
                "error": None
            }, conversation_id
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la conversation {conversation_id}: {e}")
            return {
                "error": str(e)
            }, None
    
    # Fonction pour supprimer une conversation
    def delete_conversation(conversation_id):
        if not conversation_id:
            return {
                "error": "Aucune conversation sélectionnée"
            }, None
        
        try:
            api_client.delete_conversation(conversation_id)
            conversations = api_client.list_conversations()
            
            return {
                "conversations": conversations,
                "current_conversation_id": conversations[0]["id"] if conversations else None,
                "messages": [],
                "sources": [],
                "error": None
            }, conversations[0]["id"] if conversations else None
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la conversation {conversation_id}: {e}")
            return {
                "error": str(e)
            }, None
    
    # Fonction pour envoyer un message
    def send_message(
        conversation_id, 
        message, 
        state, 
        llm_config_id,
        active_rags,
        active_notes
    ):
        if not conversation_id:
            return message, {
                "error": "Veuillez sélectionner ou créer une conversation"
            }, conversation_id
        
        if not message.strip():
            return message, state, conversation_id
        
        try:
            # Extraire seulement les IDs des listes de choix
            active_rag_ids = []
            for rag in active_rags:
                if isinstance(rag, (list, tuple)) and len(rag) > 1:
                    active_rag_ids.append(rag[1])
                else:
                    active_rag_ids.append(rag)
            
            active_note_ids = []
            for note in active_notes:
                if isinstance(note, (list, tuple)) and len(note) > 1:
                    active_note_ids.append(note[1])
                else:
                    active_note_ids.append(note)
            
            # Mise à jour de l'état (affichage immédiat du message utilisateur)
            messages = state.get("messages", []).copy()
            user_message = {
                "id": -1,  # ID temporaire
                "role": "user",
                "content": message,
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
            messages.append(user_message)
            
            # Message de chargement en attendant la réponse
            loading_message = {
                "id": -2,  # ID temporaire
                "role": "assistant",
                "content": "Génération de la réponse...",
                "is_loading": True,
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
            messages.append(loading_message)
            
            yield "", {
                "messages": messages,
                "current_conversation_id": conversation_id,
                "error": None
            }, conversation_id
            
            # Envoi du message à l'API
            response = api_client.send_message(
                conversation_id=conversation_id,
                content=message,
                llm_config_id=llm_config_id,
                active_rags=active_rag_ids,
                active_notes=active_note_ids
            )
            
            # Mise à jour des messages avec la réponse réelle
            messages = [m for m in messages if m.get("id") != -2]  # Suppression du message de chargement
            
            # Ajouter la réponse de l'assistant
            assistant_message = response.get("assistant_message", {})
            messages.append(assistant_message)
            
            # Obtenir les sources
            sources = response.get("sources", [])
            
            yield "", {
                "messages": messages,
                "sources": sources,
                "current_conversation_id": conversation_id,
                "error": None
            }, conversation_id
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du message: {e}")
            
            error_message = {
                "id": -3,  # ID temporaire
                "role": "system",
                "content": f"Erreur lors de l'envoi du message: {str(e)}",
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
            
            messages = [m for m in state.get("messages", []) if m.get("id") != -2]  # Suppression du message de chargement
            messages.append(error_message)
            
            yield "", {
                "messages": messages,
                "current_conversation_id": conversation_id,
                "error": str(e)
            }, conversation_id
    
    # Création des composants UI
    with gr.Row():
        with gr.Column(scale=1):
            # Liste des conversations
            gr.Markdown("### Conversations")
            
            conversation_list = gr.Dropdown(
                label="Conversations existantes", 
                choices=[], 
                value=None,
                interactive=True
            )
            
            new_conversation_title = gr.Textbox(
                label="Titre de la nouvelle conversation",
                placeholder="Ma nouvelle conversation"
            )
            create_button = gr.Button("Créer", variant="primary")
            
            with gr.Row():
                refresh_button = gr.Button("🔄 Rafraîchir")
                delete_button = gr.Button("🗑️ Supprimer", variant="stop")
            
            # Sélecteur de modèle LLM
            llm_selector = create_model_selector()
            
            # Sélecteur de contexte (RAG et notes)
            context_selector = create_context_selector()
        
        with gr.Column(scale=3):
            # Zone de chat - adaptation pour Gradio 5.x
            chat_box = gr.Chatbot(
                label="Conversation",
                height=500,
                avatar_images=["👤", "🧠"],  # Utilisateur, Assistant
                render=render_message,
                show_label=False,
                # bubble=True,  # désactivé pour compatibilité
                show_copy_button=True  # nouvelle fonctionnalité de Gradio 5.x
            )
            
            # Zone de saisie et bouton d'envoi
            with gr.Row():
                user_input = gr.Textbox(
                    placeholder="Posez votre question...",
                    scale=4,
                    container=False
                )
                send_button = gr.Button("Envoyer", scale=1, variant="primary")
            
            # Affichage des sources
            sources_display = gr.HTML(render_sources([]))
            
            # Message d'erreur
            error_display = gr.Markdown(visible=False)
    
    # Chargement initial des conversations
    def on_load():
        state, conv_id = load_conversations()
        
        # Mettre à jour la liste des conversations
        conversations = state.get("conversations", [])
        conversation_choices = [(c["title"], c["id"]) for c in conversations]
        current_id = state.get("current_conversation_id")
        
        # Mettre à jour la liste déroulante avec les choix
        conversation_list_updated = gr.Dropdown(
            choices=conversation_choices, 
            value=current_id
        )
        
        # Si erreur, la rendre visible
        error_visible = bool(state.get("error"))
        error_message = state.get("error", "")
        
        # Retourner exactement les 3 valeurs attendues par gradio_app.py
        return [
            conversation_list_updated,  # conversation_list
            state,  # conversation_state
            gr.Markdown(visible=error_visible, value=error_message)  # error_display
        ]
    
    # Création d'une nouvelle conversation
    def handle_create_conversation(title, llm_config_id):
        state, conv_id = create_new_conversation(title, llm_config_id)
        
        # Mettre à jour la liste des conversations
        conversations = state.get("conversations", [])
        conversation_choices = [(c["title"], c["id"]) for c in conversations]
        current_id = state.get("current_conversation_id")
        
        # Mise à jour des sources disponibles
        rag_group, note_group = context_selector["update_available_sources"](current_id, api_client)
        
        return [
            "",  # new_conversation_title
            gr.Dropdown(choices=conversation_choices, value=current_id),  # conversation_list
            state,  # conversation_state
            conv_id,  # current_conversation_id
            [],  # chat_box
            "",  # sources_display
            rag_group,  # context_selector["active_rags"]
            note_group,  # context_selector["active_notes"]
            gr.Markdown(visible=bool(state.get("error")), value=state.get("error", ""))  # error_display
        ]
    
    create_button.click(
        fn=handle_create_conversation,
        inputs=[
            new_conversation_title,
            llm_selector["selected_config_id"]
        ],
        outputs=[
            new_conversation_title,
            conversation_list,
            conversation_state,
            current_conversation_id,
            chat_box,
            sources_display,
            context_selector["active_rags"],
            context_selector["active_notes"],
            error_display
        ]
    )
    
    # Chargement d'une conversation existante
    def handle_load_conversation(conversation_id):
        # Si conversation_id est un tuple (nom, id), extraire l'id
        if isinstance(conversation_id, (list, tuple)) and len(conversation_id) > 1:
            conversation_id = conversation_id[1]
        
        state, conv_id = load_conversation(conversation_id)
        
        # Mise à jour des sources disponibles
        rag_group, note_group = context_selector["update_available_sources"](conversation_id, api_client)
        
        return [
            state,  # conversation_state
            conv_id,  # current_conversation_id
            state.get("messages", []),  # chat_box
            render_sources(state.get("sources", [])),  # sources_display
            rag_group,  # context_selector["active_rags"]
            note_group,  # context_selector["active_notes"]
            gr.Markdown(visible=bool(state.get("error")), value=state.get("error", ""))  # error_display
        ]
    
    conversation_list.change(
        fn=handle_load_conversation,
        inputs=[conversation_list],
        outputs=[
            conversation_state,
            current_conversation_id,
            chat_box,
            sources_display,
            context_selector["active_rags"],
            context_selector["active_notes"],
            error_display
        ]
    )
    
    # Suppression d'une conversation
    def handle_delete_conversation(conversation_id, state):
        if not conversation_id:
            return [
                state,
                None,
                gr.Dropdown(choices=[]),
                [],
                "",
                gr.Markdown(visible=True, value="Aucune conversation sélectionnée")
            ]
        
        result, conv_id = delete_conversation(conversation_id)
        
        # Mettre à jour la liste des conversations
        conversations = result.get("conversations", [])
        conversation_choices = [(c["title"], c["id"]) for c in conversations]
        current_id = result.get("current_conversation_id")
        
        return [
            result,  # conversation_state
            conv_id,  # current_conversation_id
            gr.Dropdown(choices=conversation_choices, value=current_id),  # conversation_list
            [],  # chat_box
            "",  # sources_display
            gr.Markdown(visible=bool(result.get("error")), value=result.get("error", ""))  # error_display
        ]
    
    delete_button.click(
        fn=handle_delete_conversation,
        inputs=[current_conversation_id, conversation_state],
        outputs=[
            conversation_state,
            current_conversation_id,
            conversation_list,
            chat_box,
            sources_display,
            error_display
        ]
    )
    
    # Rafraîchissement des conversations
    def handle_refresh_conversations():
        state, conv_id = load_conversations()
        
        # Mettre à jour la liste des conversations
        conversations = state.get("conversations", [])
        conversation_choices = [(c["title"], c["id"]) for c in conversations]
        current_id = state.get("current_conversation_id")
        
        return [
            gr.Dropdown(choices=conversation_choices, value=current_id),  # conversation_list
            state,  # conversation_state
            conv_id,  # current_conversation_id
            gr.Markdown(visible=bool(state.get("error")), value=state.get("error", ""))  # error_display
        ]
    
    refresh_button.click(
        fn=handle_refresh_conversations,
        outputs=[
            conversation_list,
            conversation_state,
            current_conversation_id,
            error_display
        ]
    )
    
    # Rafraîchissement des modèles LLM
    llm_selector["refresh_button"].click(
        fn=lambda: llm_selector["load_models"](api_client),
        outputs=[
            llm_selector["model_dropdown"],
            llm_selector["selected_config_id"]
        ]
    )
    
    # Rafraîchissement des sources disponibles
    context_selector["refresh_button"].click(
        fn=lambda conv_id: context_selector["update_available_sources"](conv_id, api_client),
        inputs=[current_conversation_id],
        outputs=[
            context_selector["active_rags"],
            context_selector["active_notes"]
        ]
    )
    
    # Envoi d'un message
    send_fn = send_message
    send_button.click(
        fn=send_fn,
        inputs=[
            current_conversation_id,
            user_input,
            conversation_state,
            llm_selector["selected_config_id"],
            context_selector["active_rags"],
            context_selector["active_notes"]
        ],
        outputs=[
            user_input,
            conversation_state,
            current_conversation_id,
            chat_box,
            sources_display,
            error_display
        ]
    )
    
    user_input.submit(
        fn=send_fn,
        inputs=[
            current_conversation_id,
            user_input,
            conversation_state,
            llm_selector["selected_config_id"],
            context_selector["active_rags"],
            context_selector["active_notes"]
        ],
        outputs=[
            user_input,
            conversation_state,
            current_conversation_id,
            chat_box,
            sources_display,
            error_display
        ]
    )
    
    # Activer/désactiver les sources RAG
    context_selector["active_rags"].change(
        fn=lambda active_rags, conv_id: context_selector["handle_rag_change"](conv_id, active_rags, api_client),
        inputs=[context_selector["active_rags"], current_conversation_id],
        outputs=[]
    )
    
    # Activer/désactiver les notes
    context_selector["active_notes"].change(
        fn=lambda active_notes, conv_id: context_selector["handle_note_change"](conv_id, active_notes, api_client),
        inputs=[context_selector["active_notes"], current_conversation_id],
        outputs=[]
    )
    
    return {
        "conversation_state": conversation_state,
        "current_conversation_id": current_conversation_id,
        "chat_box": chat_box,
        "user_input": user_input,
        "send_button": send_button,
        "conversation_list": conversation_list,
        "error_display": error_display,
        "on_load": on_load
    }