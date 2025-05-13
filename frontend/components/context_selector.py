import gradio as gr
from typing import Dict, Any, List, Tuple

def create_context_selector():
    """
    Crée un composant pour sélectionner les sources de contexte.
    
    Returns:
        Dict contenant les composants du sélecteur
    """
    with gr.Accordion("Sources RAG & Notes", open=False, elem_id="context-selector-accordion"):
        active_rags = gr.CheckboxGroup(
            label="Corpus RAG actifs",
            choices=[],
            value=[],
            # Options Gradio 5.x
            container=True,
            elem_id="active-rags-selector",
            show_label=True,
            interactive=True
        )
        
        active_notes = gr.CheckboxGroup(
            label="Notes actives",
            choices=[],
            value=[],
            # Options Gradio 5.x
            container=True,
            elem_id="active-notes-selector",
            show_label=True,
            interactive=True
        )
        
        refresh_button = gr.Button("Rafraîchir les sources", elem_id="refresh-sources-button")
    
    # Fonction pour mettre à jour les sources disponibles
    def update_available_sources(conversation_id, api_client) -> Tuple[gr.components.CheckboxGroup, gr.components.CheckboxGroup]:
        """
        Met à jour les sources disponibles pour une conversation donnée.
        
        Args:
            conversation_id: ID de la conversation
            api_client: Client API pour les requêtes
            
        Returns:
            Tuple de (CheckboxGroup RAG mis à jour, CheckboxGroup Notes mis à jour)
        """
        if not conversation_id:
            return gr.CheckboxGroup(choices=[], value=[]), gr.CheckboxGroup(choices=[], value=[])
        
        try:
            sources = api_client.get_available_sources(conversation_id)
            
            # Corpus RAG
            rag_corpus = sources.get("rag_corpus", [])
            rag_choices = [(f"{c['name']} ({c['document_count']} docs)", c["id"]) for c in rag_corpus]
            rag_values = [c["id"] for c in rag_corpus if c.get("is_active", False)]
            
            # Notes
            notes = sources.get("notes", [])
            note_choices = [(n["title"], n["id"]) for n in notes]
            note_values = [n["id"] for n in notes if n.get("is_active", False)]
            
            # Pour Gradio 5.x, retourner de nouveaux composants
            return (
                gr.CheckboxGroup(choices=rag_choices, value=rag_values, container=True, show_label=True),
                gr.CheckboxGroup(choices=note_choices, value=note_values, container=True, show_label=True)
            )
        except Exception as e:
            print(f"Erreur lors de la mise à jour des sources: {e}")
            return gr.CheckboxGroup(choices=[], value=[]), gr.CheckboxGroup(choices=[], value=[])
    
    # Fonction pour activer/désactiver une source
    def toggle_source(conversation_id, context_type, context_id, is_active, api_client):
        """
        Active ou désactive une source pour une conversation.
        
        Args:
            conversation_id: ID de la conversation
            context_type: Type de contexte ('rag' ou 'note')
            context_id: ID de la source
            is_active: État d'activation
            api_client: Client API
        """
        if not conversation_id:
            return
        
        try:
            api_client.update_context_activation(
                conversation_id=conversation_id,
                context_type=context_type,
                context_id=context_id,
                is_active=is_active
            )
        except Exception as e:
            print(f"Erreur: {str(e)}")
    
    # Fonction pour traiter les changements de sélection RAG
    def handle_rag_change(conversation_id, selected_values, api_client):
        """
        Gère les changements de sélection des corpus RAG.
        
        Args:
            conversation_id: ID de la conversation
            selected_values: Valeurs sélectionnées
            api_client: Client API
        """
        if not conversation_id:
            return
        
        try:
            # Récupérer les sources disponibles
            sources = api_client.get_available_sources(conversation_id)
            rag_corpus = sources.get("rag_corpus", [])
            
            # Extraire les IDs de la liste de sélection
            selected_ids = []
            for value in selected_values:
                if isinstance(value, (list, tuple)) and len(value) > 1:
                    selected_ids.append(value[1])
                else:
                    selected_ids.append(value)
            
            # Pour chaque corpus RAG, mettre à jour son état d'activation
            for corpus in rag_corpus:
                corpus_id = corpus["id"]
                is_active = corpus_id in selected_ids
                
                # Mettre à jour l'activation seulement si nécessaire
                if is_active != corpus.get("is_active", False):
                    api_client.update_context_activation(
                        conversation_id=conversation_id,
                        context_type="rag",
                        context_id=corpus_id,
                        is_active=is_active
                    )
        except Exception as e:
            print(f"Erreur: {str(e)}")
    
    # Fonction pour traiter les changements de sélection des notes
    def handle_note_change(conversation_id, selected_values, api_client):
        """
        Gère les changements de sélection des notes.
        
        Args:
            conversation_id: ID de la conversation
            selected_values: Valeurs sélectionnées
            api_client: Client API
        """
        if not conversation_id:
            return
        
        try:
            # Récupérer les sources disponibles
            sources = api_client.get_available_sources(conversation_id)
            notes = sources.get("notes", [])
            
            # Extraire les IDs de la liste de sélection
            selected_ids = []
            for value in selected_values:
                if isinstance(value, (list, tuple)) and len(value) > 1:
                    selected_ids.append(value[1])
                else:
                    selected_ids.append(value)
            
            # Pour chaque note, mettre à jour son état d'activation
            for note in notes:
                note_id = note["id"]
                is_active = note_id in selected_ids
                
                # Mettre à jour l'activation seulement si nécessaire
                if is_active != note.get("is_active", False):
                    api_client.update_context_activation(
                        conversation_id=conversation_id,
                        context_type="note",
                        context_id=note_id,
                        is_active=is_active
                    )
        except Exception as e:
            print(f"Erreur: {str(e)}")
    
    return {
        "active_rags": active_rags,
        "active_notes": active_notes,
        "refresh_button": refresh_button,
        "update_available_sources": update_available_sources,
        "handle_rag_change": handle_rag_change,
        "handle_note_change": handle_note_change
    }