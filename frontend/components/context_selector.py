import gradio as gr
from typing import Dict, Any, List

def create_context_selector():
    """
    Crée un composant pour sélectionner les sources de contexte.
    
    Returns:
        Dict contenant les composants du sélecteur
    """
    with gr.Accordion("Sources RAG & Notes", open=False):
        active_rags = gr.CheckboxGroup(
            label="Corpus RAG actifs",
            choices=[],
            value=[]
        )
        
        active_notes = gr.CheckboxGroup(
            label="Notes actives",
            choices=[],
            value=[]
        )
        
        refresh_button = gr.Button("Rafraîchir les sources")
    
    # Fonction pour mettre à jour les sources disponibles
    def update_available_sources(conversation_id, api_client):
        if not conversation_id:
            return gr.CheckboxGroup(choices=[]), gr.CheckboxGroup(choices=[])
        
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
            
            return (
                gr.CheckboxGroup(choices=rag_choices, value=rag_values),
                gr.CheckboxGroup(choices=note_choices, value=note_values)
            )
        except Exception as e:
            print(f"Erreur lors de la mise à jour des sources: {e}")
            return gr.CheckboxGroup(choices=[]), gr.CheckboxGroup(choices=[])
    
    return {
        "active_rags": active_rags,
        "active_notes": active_notes,
        "refresh_button": refresh_button,
        "update_available_sources": update_available_sources
    }