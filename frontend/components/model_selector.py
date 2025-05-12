import gradio as gr
from typing import Dict, Any, List

def create_model_selector():
    """
    Crée un composant pour sélectionner un modèle LLM.
    
    Returns:
        Dict contenant les composants du sélecteur
    """
    # État pour stocker l'ID de configuration sélectionné
    selected_config_id = gr.State(None)
    
    # En-tête
    gr.Markdown("### Modèle LLM")
    
    # Dropdown pour sélectionner le modèle
    with gr.Row():
        model_dropdown = gr.Dropdown(
            label="Modèle à utiliser",
            choices=[],
            value=None,
            interactive=True
        )
        
        refresh_button = gr.Button("🔄", scale=1)
    
    # Fonction pour mettre à jour la liste des modèles
    def load_models(api_client):
        try:
            configs = api_client.list_llm_configs()
            return gr.Dropdown(
                choices=[(c["name"], c["id"]) for c in configs],
                value=configs[0]["id"] if configs else None
            ), configs[0]["id"] if configs else None
        except Exception:
            return gr.Dropdown(choices=[]), None
    
    return {
        "selected_config_id": selected_config_id,
        "model_dropdown": model_dropdown,
        "refresh_button": refresh_button,
        "load_models": load_models
    }