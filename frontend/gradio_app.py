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
    
    # Création de l'application
    with gr.Blocks(
        title=title, 
        theme=gr.themes.Soft(), 
        css=open(os.path.join(os.path.dirname(__file__), "assets/styles.css"), "r").read()
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
        
        gr.on(
            gr.triggers.Loads,
            fn=check_api,
            outputs=[api_status]
        )
        
        # Onglets
        with gr.Tabs():
            with gr.TabItem("Conversations"):
                chat_interface = create_chat_interface(api_client)
            
            with gr.TabItem("Gestion RAG"):
                rag_manager = create_rag_manager(api_client)
            
            with gr.TabItem("Configurations LLM"):
                llm_config = create_llm_config(api_client)
            
            with gr.TabItem("Notes"):
                notes_manager = create_notes_manager(api_client)
        
        # Pied de page
        gr.Markdown("---")
        gr.Markdown("© 2024 SCIRAG - Développé avec Gradio et FastAPI")
    
    return app

if __name__ == "__main__":
    # Création et lancement de l'application
    app = create_app()
    
    # Vérification initiale de la connexion à l'API
    api_client = APIClient(API_URL)
    if api_client.check_health():
        logger.info(f"✅ Connecté à l'API: {API_URL}")
        app.launch(server_name="0.0.0.0", server_port=8501)
    else:
        logger.error(f"❌ Impossible de se connecter à l'API: {API_URL}")
        logger.error("Veuillez démarrer le backend avant le frontend.")
        
        # Lancer quand même l'application avec un avertissement
        logger.info("Lancement de l'application en mode dégradé...")
        app.launch(server_name="0.0.0.0", server_port=8501)