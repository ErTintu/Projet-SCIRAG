import gradio as gr
import logging
from typing import List, Dict, Any
from services.utils import format_timestamp

logger = logging.getLogger(__name__)

def create_llm_config(api_client):
    """
    Crée l'interface de configuration des modèles LLM.
    
    Args:
        api_client: Instance du client API
        
    Returns:
        Dict contenant les composants de l'interface
    """
    # État des configurations LLM
    llm_state = gr.State({
        "llm_configs": [],
        "providers": [],
        "current_config_id": None,
        "current_config_details": None,
        "error": None
    })
    
    # Fonction pour charger les configurations LLM
    def load_llm_configs():
        try:
            llm_configs = api_client.list_llm_configs()
            providers = api_client.list_llm_providers()
            
            return {
                "llm_configs": llm_configs,
                "providers": providers,
                "current_config_id": llm_configs[0]["id"] if llm_configs else None,
                "error": None
            }
        except Exception as e:
            logger.error(f"Erreur lors du chargement des configurations LLM: {e}")
            return {
                "llm_configs": [],
                "providers": [],
                "current_config_id": None,
                "error": str(e)
            }
    
    # Fonction pour créer une nouvelle configuration LLM
    def create_llm_config(name, provider, model_name, api_key, api_url, temperature, max_tokens):
        if not name or not provider or not model_name:
            return "Nom, provider et modèle sont obligatoires", llm_state.value
        
        try:
            new_config = api_client.create_llm_config(
                name=name,
                provider=provider,
                model_name=model_name,
                api_key=api_key if api_key else None,
                api_url=api_url if api_url else None,
                temperature=float(temperature),
                max_tokens=int(max_tokens)
            )
            
            llm_configs = api_client.list_llm_configs()
            
            return "Configuration créée avec succès", {
                "llm_configs": llm_configs,
                "current_config_id": new_config["id"],
                "current_config_details": new_config,
                "error": None
            }
        except Exception as e:
            logger.error(f"Erreur lors de la création de la configuration LLM: {e}")
            return f"Erreur: {str(e)}", llm_state.value
    
    # Fonction pour mettre à jour la liste des modèles disponibles
    def update_models_list(provider, state):
        providers = state.get("providers", [])
        
        # Trouver le provider sélectionné
        selected_provider = None
        for p in providers:
            if p["id"] == provider:
                selected_provider = p
                break
        
        if not selected_provider:
            return []
        
        # Retourner la liste des modèles pour ce provider
        return selected_provider.get("models", [])
    
    # Fonction pour charger les détails d'une configuration LLM
    def load_llm_config_details(config_id):
        if not config_id:
            return {
                "current_config_id": None,
                "current_config_details": None,
                "error": None
            }
        
        try:
            config = api_client.get_llm_config(config_id)
            
            return {
                "current_config_id": config_id,
                "current_config_details": config,
                "error": None
            }
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration LLM {config_id}: {e}")
            return {
                "error": str(e)
            }
    
    # Interface
    with gr.Row():
        with gr.Column(scale=1):
            # Liste des configurations
            with gr.Group(title="Configurations existantes"):
                config_dropdown = gr.Dropdown(
                    label="Sélectionner une configuration",
                    choices=[],
                    value=None,
                    interactive=True
                )
                refresh_button = gr.Button("🔄 Rafraîchir")
            
            # Détails de la configuration sélectionnée
            with gr.Group(title="Détails"):
                config_details = gr.HTML()
        
        with gr.Column(scale=2):
            # Création de configuration
            with gr.Group(title="Créer une nouvelle configuration"):
                config_name = gr.Textbox(label="Nom")
                
                with gr.Row():
                    provider_dropdown = gr.Dropdown(
                        label="Provider",
                        choices=[]
                    )
                    model_dropdown = gr.Dropdown(
                        label="Modèle",
                        choices=[]
                    )
                
                with gr.Row():
                    api_key = gr.Textbox(
                        label="Clé API",
                        placeholder="Optionnel pour les modèles locaux",
                        type="password"
                    )
                    api_url = gr.Textbox(
                        label="URL API",
                        placeholder="Pour les modèles locaux (LM Studio)"
                    )
                
                with gr.Row():
                    temperature = gr.Slider(
                        label="Température",
                        minimum=0.0,
                        maximum=1.0,
                        value=0.7,
                        step=0.05
                    )
                    max_tokens = gr.Slider(
                        label="Tokens max",
                        minimum=100,
                        maximum=4000,
                        value=1024,
                        step=100
                    )
                
                create_config_button = gr.Button("Créer", variant="primary")
                status_message = gr.Textbox(
                    label="Statut",
                    interactive=False
                )
    
    # Chargement initial
    def on_load():
        state = load_llm_configs()
        
        # Mettre à jour la liste des configurations
        llm_configs = state.get("llm_configs", [])
        config_choices = [(c["name"], c["id"]) for c in llm_configs]
        current_id = state.get("current_config_id")
        
        # Mettre à jour la liste des providers
        providers = state.get("providers", [])
        provider_choices = [(p["name"], p["id"]) for p in providers]
        
        # Mettre à jour l'affichage d'erreur
        error = state.get("error")
        error_message = f"Erreur: {error}" if error else ""
        
        return [
            state,  # llm_state
            gr.Dropdown(choices=config_choices, value=current_id),  # config_dropdown
            gr.Dropdown(choices=provider_choices),  # provider_dropdown
            error_message  # status_message
        ]
    
    gr.on(
        gr.triggers.Loads,
        fn=on_load,
        outputs=[
            llm_state,
            config_dropdown,
            provider_dropdown,
            status_message
        ]
    )
    
    # Événements
    create_config_button.click(
        fn=create_llm_config,
        inputs=[
            config_name, 
            provider_dropdown,
            model_dropdown,
            api_key,
            api_url,
            temperature,
            max_tokens
        ],
        outputs=[status_message, llm_state]
    )
    
    refresh_button.click(
        fn=load_llm_configs,
        outputs=[llm_state]
    )
    
    # Mise à jour des modèles disponibles lorsque le provider change
    provider_dropdown.change(
        fn=update_models_list,
        inputs=[provider_dropdown, llm_state],
        outputs=[model_dropdown]
    )
    
    # Chargement d'une configuration lorsqu'elle est sélectionnée
    def handle_config_selection(config_id):
        updates = load_llm_config_details(config_id)
        config_details = updates.get("current_config_details")
        
        # Mettre à jour les détails de la configuration
        if config_details:
            html = f"""
            <div class='config-details'>
                <h3>{config_details['name']}</h3>
                <p><strong>Provider:</strong> {config_details['provider']}</p>
                <p><strong>Modèle:</strong> {config_details['model_name']}</p>
                <p><strong>Température:</strong> {config_details.get('temperature', 0.7)}</p>
                <p><strong>Tokens max:</strong> {config_details.get('max_tokens', 1024)}</p>
                <p><strong>URL API:</strong> {config_details.get('api_url', 'Non définie')}</p>
                <p><strong>Créée le:</strong> {format_timestamp(config_details.get('created_at', ''))}</p>
            </div>
            """
        else:
            html = "Sélectionnez une configuration pour voir les détails"
        
        return [
            updates,  # llm_state
            html,  # config_details
        ]
    
    config_dropdown.change(
        fn=handle_config_selection,
        inputs=[config_dropdown],
        outputs=[
            llm_state,
            config_details
        ]
    )
    
    # Surveillance de l'état pour mettre à jour l'interface
    def update_config_dropdown(state):
        configs = state.get("llm_configs", [])
        return gr.Dropdown(
            choices=[(c["name"], c["id"]) for c in configs],
            value=state.get("current_config_id")
        )
    
    def update_provider_dropdown(state):
        providers = state.get("providers", [])
        return gr.Dropdown(
            choices=[(p["name"], p["id"]) for p in providers]
        )
    
    def update_config_details(state):
        details = state.get("current_config_details")
        
        if not details:
            return "Sélectionnez une configuration pour voir les détails"
        
        html = f"""
        <div class='config-details'>
            <h3>{details['name']}</h3>
            <p><strong>Provider:</strong> {details['provider']}</p>
            <p><strong>Modèle:</strong> {details['model_name']}</p>
            <p><strong>Température:</strong> {details.get('temperature', 0.7)}</p>
            <p><strong>Tokens max:</strong> {details.get('max_tokens', 1024)}</p>
            <p><strong>URL API:</strong> {details.get('api_url', 'Non définie')}</p>
            <p><strong>Créée le:</strong> {format_timestamp(details.get('created_at', ''))}</p>
        </div>
        """
        
        return html
    
    # Mise à jour de l'interface en fonction de l'état
    llm_state.change(
        fn=update_config_dropdown,
        inputs=[llm_state],
        outputs=[config_dropdown]
    )
    
    llm_state.change(
        fn=update_provider_dropdown,
        inputs=[llm_state],
        outputs=[provider_dropdown]
    )
    
    llm_state.change(
        fn=update_config_details,
        inputs=[llm_state],
        outputs=[config_details]
    )
    
    return {
        "llm_state": llm_state,
        "config_dropdown": config_dropdown
    }