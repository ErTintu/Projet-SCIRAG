import gradio as gr
import os
import logging
from dotenv import load_dotenv

# Import des services
from services.api_client import APIClient

# Import des pages
from pages.chat_interface import create_chat_interface
from pages.rag_manager import create_rag_manager
from pages.llm_config import create_llm_config
from pages.notes_manager import create_notes_manager

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Chargement des variables d'environnement
load_dotenv()

# Configuration de l'API
API_URL = os.getenv("API_URL", "http://localhost:8000")

def create_app():
    """Crée l'application Gradio."""
    
    # Initialisation du client API
    api_client = APIClient(API_URL)
    
    # Configuration du titre et du thème
    title = "🧠 SCIRAG - Assistant Conversationnel Intelligent"
    description = """
    SCIRAG est un assistant conversationnel basé sur les LLMs (Claude, GPT, etc.), 
    enrichi par la recherche de documents via RAG (Retrieval-Augmented Generation) 
    et l'intégration de notes personnelles activables.
    """
    
    # Création de l'application avec compatibilité Gradio 5.x
    with gr.Blocks(
        title=title, 
        theme=gr.themes.Soft(), 
        css=open(os.path.join(os.path.dirname(__file__), "assets/styles.css"), "r").read() if os.path.exists(os.path.join(os.path.dirname(__file__), "assets/styles.css")) else "",
        analytics_enabled=False,  # Nouvelle option Gradio 5.x
        head=[  # Nouvelle option Gradio 5.x pour ajouter du contenu au head HTML
            """
            <meta name="description" content="SCIRAG - Assistant Conversationnel Intelligent basé sur RAG">
            <meta name="author" content="SCIRAG">
            <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🧠</text></svg>">
            """
        ]
    ) as app:
        gr.Markdown(f"# {title}")
        gr.Markdown(description)
        
        # Vérification de l'état de l'API
        api_status = gr.Markdown("🔄 Vérification de la connexion à l'API...")
        
        # Fonction pour vérifier l'état de l'API
        def check_api():
            if api_client.check_health():
                return f"✅ Connecté à l'API: {API_URL}"
            else:
                return f"❌ Impossible de se connecter à l'API: {API_URL}"
        
        # Utilisation de app.load() avec Gradio 5.x
        app.load(fn=check_api, outputs=api_status)
        
        # Section pour les onglets dans gradio_app.py - avec TabItem mis à jour pour Gradio 5.x
        with gr.Tabs(selected=0) as tabs:  # selected est un paramètre Gradio 5.x
            with gr.Tab("Conversations", id="tab-conversations"):  # Utilisation de Tab au lieu de TabItem pour Gradio 5.x
                chat_interface = create_chat_interface(api_client)
                
                # Filtrer les sorties valides (non None)
                outputs = [
                    chat_interface["conversation_list"],
                    chat_interface["conversation_state"],
                    chat_interface["error_display"]
                ]
                
                # Configuration de l'événement de chargement pour l'interface de chat
                app.load(
                    fn=chat_interface["on_load"],
                    outputs=outputs
                )
            
            with gr.Tab("Gestion RAG", id="tab-rag"):  # Utilisation de Tab au lieu de TabItem pour Gradio 5.x
                rag_manager = create_rag_manager(api_client)
                
                # Configuration de l'événement de chargement pour le gestionnaire RAG
                app.load(
                    fn=rag_manager["on_load"],
                    outputs=rag_manager["on_load_outputs"]
                )
                
                # Pas besoin de rafraîchissement supplémentaire si on_load est bien implémenté
                            
            with gr.Tab("Configurations LLM", id="tab-llm"):  # Utilisation de Tab au lieu de TabItem pour Gradio 5.x
                llm_config = create_llm_config(api_client)
                
                # Configuration de l'événement de chargement pour la configuration LLM
                app.load(
                    fn=llm_config["on_load"],
                    outputs=[
                        llm_config["llm_state"],
                        llm_config["current_config_id"],
                        llm_config["config_dropdown"],
                        llm_config["provider_dropdown"]
                    ]
                )
                
                # Déclencher la mise à jour des composants après le chargement
                llm_config["llm_state"].change(lambda x: None, inputs=[llm_config["llm_state"]], outputs=[])
            
            with gr.Tab("Notes", id="tab-notes"):  # Utilisation de Tab au lieu de TabItem pour Gradio 5.x
                notes_manager = create_notes_manager(api_client)
                
                # Configuration de l'événement de chargement pour le gestionnaire de notes
                app.load(
                    fn=notes_manager["on_load"],
                    outputs=[
                        notes_manager["notes_state"],
                        notes_manager["current_note_id"]
                    ]
                )
                
                # Déclencher la mise à jour des composants après le chargement
                notes_manager["notes_state"].change(lambda x: None, inputs=[notes_manager["notes_state"]], outputs=[])
                
        # Pied de page
        gr.Markdown("---")
        with gr.Row():
            gr.Markdown("© 2025 SCIRAG - Développé avec Gradio et FastAPI")
            # Ajout d'un lien vers la documentation API (Swagger) - fonctionnalité Gradio 5.x
            gr.HTML(f'<div style="text-align: right;"><a href="{API_URL}/docs" target="_blank">📚 Documentation API</a></div>')
    
    return app

if __name__ == "__main__":
    # Création et lancement de l'application
    app = create_app()
    
    # Vérification initiale de la connexion à l'API
    api_client = APIClient(API_URL)
    if api_client.check_health():
        logger.info(f"✅ Connecté à l'API: {API_URL}")
        # Options de lancement simplifiées - suppression de enable_queue qui cause une erreur
        app.launch(
            server_name="0.0.0.0",
            server_port=8501,
            favicon_path=None,
            share=False,
            debug=False,
            auth=None,
            quiet=False,
            show_error=True
        )
    else:
        logger.error(f"❌ Impossible de se connecter à l'API: {API_URL}")
        logger.error("Veuillez démarrer le backend avant le frontend.")
        
        # Lancer quand même l'application avec un avertissement
        logger.info("Lancement de l'application en mode dégradé...")
        app.launch(
            server_name="0.0.0.0",
            server_port=8501,
            share=False
        )