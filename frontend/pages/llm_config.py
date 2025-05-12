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
        "current_config_details": None,
        "error": None
    })
    
    # État séparé pour l'ID de la configuration actuelle
    current_config_id = gr.State(None)
    
    # Fonction pour charger les configurations LLM
    def load_llm_configs():
        try:
            llm_configs = api_client.list_llm_configs()
            providers = api_client.list_llm_providers()
            
            # ID de config à sélectionner
            selected_id = llm_configs[0]["id"] if llm_configs else None
            
            # Préparer les données d'état
            state = {
                "llm_configs": llm_configs,
                "providers": providers,
                "error": None
            }
            
            return state, selected_id
        except Exception as e:
            logger.error(f"Erreur lors du chargement des configurations LLM: {e}")
            return {
                "llm_configs": [],
                "providers": [],
                "error": str(e)
            }, None
    
    # Fonction pour créer une nouvelle configuration LLM
    def create_llm_config(name, provider, model_name, api_key, api_url, temperature, max_tokens):
        if not name or not provider or not model_name:
            return "Nom, provider et modèle sont obligatoires", llm_state.value, current_config_id.value
        
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
                "providers": llm_state.value.get("providers", []),
                "current_config_details": new_config,
                "error": None
            }, new_config["id"]
        except Exception as e:
            logger.error(f"Erreur lors de la création de la configuration LLM: {e}")
            return f"Erreur: {str(e)}", llm_state.value, current_config_id.value
    
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
    def load_llm_config_details(config_id, current_state):
        # Vérifier si config_id est une liste ou un tuple et extraire l'ID si nécessaire
        if isinstance(config_id, (list, tuple)) and len(config_id) > 1:
            config_id = config_id[1]
            
        if not config_id:
            return {
                "current_config_details": None,
                "error": None,
                "llm_configs": current_state.get("llm_configs", []),
                "providers": current_state.get("providers", [])
            }, None
        
        try:
            config = api_client.get_llm_config(config_id)
            
            updated_state = current_state.copy()
            updated_state.update({
                "current_config_details": config,
                "error": None
            })
            
            return updated_state, config_id
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration LLM {config_id}: {e}")
            updated_state = current_state.copy()
            updated_state.update({
                "error": str(e)
            })
            return updated_state, config_id
    
    # Interface
    with gr.Row():
        with gr.Column(scale=1):
            # Liste des configurations
            gr.Markdown("### Configurations existantes")
            
            config_dropdown = gr.Dropdown(
                label="Sélectionner une configuration",
                choices=[],
                value=None,
                interactive=True,
                allow_custom_value=True
            )
            refresh_button = gr.Button("🔄 Rafraîchir")
            
            # Détails de la configuration sélectionnée
            gr.Markdown("### Détails")
            
            config_details = gr.HTML()
        
        with gr.Column(scale=2):
            # Création de configuration
            gr.Markdown("### Créer une nouvelle configuration")
            
            config_name = gr.Textbox(label="Nom")
            
            with gr.Row():
                provider_dropdown = gr.Dropdown(
                    label="Provider",
                    choices=[],
                    value=None,
                    allow_custom_value=True
                )
                model_dropdown = gr.Dropdown(
                    label="Modèle",
                    choices=[],
                    value=None,
                    allow_custom_value=True
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
    
    # Fonction pour initialiser l'interface (appelée par gradio_app.py)
    def on_load():
        """Fonction de chargement initiale pour llm_config.py"""
        state, selected_id = load_llm_configs()
        
        # Extraire les données pour les dropdowns
        configs = state.get("llm_configs", [])
        providers = state.get("providers", [])
        
        config_choices = [(c["name"], c["id"]) for c in configs]
        provider_choices = [(p["name"], p["id"]) for p in providers]
        
        # Retourner les 4 valeurs attendues par gradio_app.py
        return state, selected_id, config_choices, provider_choices
    
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
        outputs=[status_message, llm_state, current_config_id]
    )
    
    # Événement de rafraîchissement
    def handle_refresh():
        state, selected_id = load_llm_configs()
        # Préparer les choix pour les dropdowns
        config_choices = [(c["name"], c["id"]) for c in state.get("llm_configs", [])]
        provider_choices = [(p["name"], p["id"]) for p in state.get("providers", [])]
        return state, selected_id, config_choices, provider_choices, "Configurations rafraîchies"
    
    refresh_button.click(
        fn=handle_refresh,
        outputs=[llm_state, current_config_id, config_dropdown, provider_dropdown, status_message]
    )
    
    # Mise à jour des modèles disponibles lorsque le provider change
    provider_dropdown.change(
        fn=update_models_list,
        inputs=[provider_dropdown, llm_state],
        outputs=[model_dropdown]
    )
    
    # Chargement d'une configuration lorsqu'elle est sélectionnée
    def handle_config_selection(config_id, current_state):
        # Si config_id est une liste ou un tuple, extraire seulement l'ID numérique
        if isinstance(config_id, (list, tuple)) and len(config_id) > 1:
            config_id = config_id[1]  # L'ID est en position 1 dans le tuple ('nom', id)
        
        if not config_id:
            return current_state, None, "Aucune configuration sélectionnée"
        
        updated_state, config_id = load_llm_config_details(config_id, current_state)
        
        # Générer le HTML des détails
        details = updated_state.get("current_config_details")
        if details:
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
        else:
            html = "Aucun détail disponible"
        
        return updated_state, config_id, html
    
    # Mise à jour automatique des dropdowns après changement d'état
    def update_dropdowns(state):
        # Mettre à jour la liste des configurations
        configs = state.get("llm_configs", [])
        config_choices = [(c["name"], c["id"]) for c in configs]
        
        # Mettre à jour la liste des providers
        providers = state.get("providers", [])
        provider_choices = [(p["name"], p["id"]) for p in providers]
        
        # IMPORTANT: Retourner les listes de choix, pas des objets Dropdown complets
        return config_choices, provider_choices
    llm_state.change(
        fn=update_dropdowns,
        inputs=[llm_state],
        outputs=[config_dropdown, provider_dropdown]
    )
    
    # Retourne les composants qui doivent être accessibles depuis l'extérieur
    return {
        "llm_state": llm_state,
        "current_config_id": current_config_id,
        "config_dropdown": config_dropdown,
        "provider_dropdown": provider_dropdown,
        "status_message": status_message,
        "on_load": on_load
    }