import gradio as gr
from typing import Dict, Any, List

def create_model_selector():
    """
    Crée un composant pour sélectionner un modèle LLM.
    
    Returns:
        Dict contenant les composants du sélecteur
    """
    with gr.Group(title="Modèle LLM"):
        selected_config_id = gr.State(None)
        
        with gr.Row():
            model_dropdown = gr.Dropdown(
                label="Modèle à utiliser",
                choices=[],
                value=None,
                interactive=True
            )
            
            refresh_button = gr.Button("🔄", scale=0.1)
    
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