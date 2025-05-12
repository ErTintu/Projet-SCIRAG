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
        
        app.load(fn=check_api, outputs=api_status)
        
        # Section pour les onglets dans gradio_app.py
        with gr.Tabs():
            with gr.TabItem("Conversations"):
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
            
            with gr.TabItem("Gestion RAG"):
                rag_manager = create_rag_manager(api_client)
                
                # Configuration de l'événement de chargement pour le gestionnaire RAG
                # Utiliser on_load_outputs s'il existe, sinon utiliser la liste explicite
                app.local(
                    fn=rag_manager["on_load",
                                   outputs=[
                                       rag_manager["rag_state"],
                    rag_manager["current_corpus_id"],
                    rag_manager["corpus_list_html"],
                    rag_manager["corpus_buttons"],
                    rag_manager["corpus_info"],
                    rag_manager["documents_table"]]]
                )
                rag_outputs = rag_manager.get("on_load", [
                    rag_manager["rag_state"],
                    rag_manager["current_corpus_id"],
                    rag_manager["corpus_list_html"],
                    rag_manager["corpus_buttons"],
                    rag_manager["corpus_info"],
                    rag_manager["documents_table"]
                ])
                
                app.load(
                    fn=rag_manager["on_load"],
                    outputs=rag_outputs
                )
                
                # Déclencher la mise à jour des composants après le chargement
                rag_manager["rag_state"].change(lambda x: None, inputs=[rag_manager["rag_state"]], outputs=[])
            
            with gr.TabItem("Configurations LLM"):
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
            
            with gr.TabItem("Notes"):
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
        gr.Markdown("© 2025 SCIRAG - Développé avec Gradio et FastAPI")
    
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