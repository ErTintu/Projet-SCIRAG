import gradio as gr
from typing import Dict, Any, List, Tuple, Optional, Union

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
    
    # Dropdown pour sélectionner le modèle avec Gradio 5.x
    with gr.Row():
        model_dropdown = gr.Dropdown(
            label="Modèle à utiliser",
            choices=[],
            value=None,
            interactive=True,
            allow_custom_value=True,
            # Nouvelles options Gradio 5.x
            container=True,
            filterable=True,
            show_label=True,
            elem_id="model-selector-dropdown"
        )
        
        refresh_button = gr.Button("🔄", scale=1, elem_id="refresh-models-button")
    
    # Fonction pour mettre à jour la liste des modèles
    def load_models(api_client) -> Tuple[gr.components.Dropdown, Optional[int]]:
        """
        Charge les configurations LLM disponibles depuis l'API.
        
        Args:
            api_client: Client API pour les requêtes
            
        Returns:
            Tuple de (Dropdown mis à jour, ID de configuration sélectionné)
        """
        try:
            configs = api_client.list_llm_configs()
            choices = [(c["name"], c["id"]) for c in configs]
            selected_id = configs[0]["id"] if configs else None
            
            # Pour Gradio 5.x, on retourne une nouvelle définition de dropdown
            dropdown = gr.Dropdown(
                choices=choices,
                value=selected_id,
                interactive=True,
                allow_custom_value=True,
                filterable=True,
                container=True,
                show_label=True
            )
            
            return dropdown, selected_id
        except Exception as e:
            print(f"Erreur lors du chargement des modèles LLM: {e}")
            return gr.Dropdown(choices=[]), None
    
    # Fonction pour gérer la sélection d'un modèle
    def handle_model_selection(value) -> int:
        """
        Gère la sélection d'un modèle dans le dropdown.
        
        Args:
            value: Valeur sélectionnée (peut être un tuple (nom, id) ou directement un id)
            
        Returns:
            ID de configuration sélectionné
        """
        if isinstance(value, (list, tuple)) and len(value) > 1:
            # Si c'est un tuple (nom, id), extraire l'id
            return value[1]
        return value
    
    # Attacher le gestionnaire d'événements pour mettre à jour l'ID sélectionné
    model_dropdown.change(
        fn=handle_model_selection,
        inputs=[model_dropdown],
        outputs=[selected_config_id]
    )
    
    return {
        "selected_config_id": selected_config_id,
        "model_dropdown": model_dropdown,
        "refresh_button": refresh_button,
        "load_models": load_models
    }