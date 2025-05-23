import gradio as gr
import os
import logging
from typing import List, Dict, Any

from services.utils import format_timestamp, truncate_text

logger = logging.getLogger(__name__)

def create_rag_manager(api_client):
    """
    Crée l'interface de gestion des corpus RAG.
    
    Args:
        api_client: Instance du client API
        
    Returns:
        Dict contenant les composants de l'interface
    """
    # État des corpus RAG
    rag_state = gr.State({
        "corpus_list": [],
        "current_corpus_id": None,
        "current_corpus_details": None,
        "documents": [],
        "error": None
    })
    
    # État pour stocker l'ID du corpus courant
    current_corpus_id = gr.State(None)
    
    # Fonction pour charger les corpus
    def load_corpus_list():
        try:
            corpus_list = api_client.list_rag_corpus()
            return {
                "corpus_list": corpus_list,
                "current_corpus_id": corpus_list[0]["id"] if corpus_list else None,
                "error": None
            }, corpus_list[0]["id"] if corpus_list else None
        except Exception as e:
            logger.error(f"Erreur lors du chargement des corpus: {e}")
            return {
                "corpus_list": [],
                "current_corpus_id": None,
                "error": str(e)
            }, None
    
    # Fonction pour créer un nouveau corpus
    def create_corpus(name, description, state_value):
        if not name:
            return "Le nom ne peut pas être vide", state_value, None
        
        try:
            new_corpus = api_client.create_rag_corpus(name, description)
            corpus_list = api_client.list_rag_corpus()
            
            return "Corpus créé avec succès", {
                "corpus_list": corpus_list,
                "current_corpus_id": new_corpus["id"],
                "current_corpus_details": new_corpus,
                "documents": [],
                "error": None
            }, new_corpus["id"]
        except Exception as e:
            logger.error(f"Erreur lors de la création du corpus: {e}")
            return f"Erreur: {str(e)}", state_value, None
    
    # Fonction pour charger les détails d'un corpus
    def load_corpus_details(corpus_id):
        if not corpus_id:
            return {
                "current_corpus_id": None,
                "current_corpus_details": None,
                "documents": [],
                "error": None
            }, None
        
        try:
            logger.info(f"Chargement du corpus {corpus_id}")
            corpus_details = api_client.get_rag_corpus(corpus_id)
            return {
                "current_corpus_id": corpus_id,
                "current_corpus_details": corpus_details,
                "documents": corpus_details.get("documents", []),
                "error": None
            }, corpus_id
        except Exception as e:
            logger.error(f"Erreur lors du chargement du corpus {corpus_id}: {e}")
            return {
                "error": str(e)
            }, None
    
    # Fonction pour uploader un document
    def upload_document(files, corpus_id):
        if not corpus_id:
            return "Veuillez d'abord sélectionner un corpus", None, None
        
        if not files:
            return "Aucun fichier sélectionné", None, None
        
        results = []
        for file_obj in files:
            file_path = file_obj.name
            file_name = os.path.basename(file_path)
            
            try:
                result = api_client.upload_document(corpus_id, file_path)
                results.append(f"✅ {file_name}: {result.get('message', 'Uploadé avec succès')}")
            except Exception as e:
                logger.error(f"Erreur lors de l'upload du document {file_name}: {e}")
                results.append(f"❌ {file_name}: {str(e)}")
        
        # Recharger les détails du corpus
        updates, corpus_id_updated = load_corpus_details(corpus_id)
        
        return "\n".join(results), updates, corpus_id_updated
    
    # Fonction pour supprimer un document
    def delete_document(document_id, corpus_id):
        if not corpus_id or not document_id:
            return "Veuillez sélectionner un corpus et un document", None, None
        
        try:
            result = api_client.delete_document(corpus_id, document_id)
            if result:
                message = f"Document {document_id} supprimé avec succès"
            else:
                message = f"Échec de la suppression du document {document_id}"
            
            # Recharger les détails du corpus
            updates, corpus_id_updated = load_corpus_details(corpus_id)
            
            return message, updates, corpus_id_updated
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du document {document_id}: {e}")
            return f"Erreur: {str(e)}", None, None
    
    # Interface
    with gr.Row():
        with gr.Column(scale=1):
            # Création d'un nouveau corpus
            gr.Markdown("### Créer un nouveau corpus")
            
            corpus_name = gr.Textbox(label="Nom du corpus")
            corpus_description = gr.Textbox(
                label="Description",
                placeholder="Description optionnelle du corpus",
                lines=3
            )
            create_corpus_button = gr.Button("Créer corpus", variant="primary")
            create_status = gr.Textbox(
                label="Statut",
                interactive=False
            )
            
            # Liste des corpus existants
            gr.Markdown("### Corpus existants")
            
            # Utilisation d'une liste déroulante au lieu du HTML pour la sélection
            corpus_dropdown = gr.Dropdown(
                label="Sélectionner un corpus",
                choices=[],
                value=None,
                interactive=True
            )
            
            refresh_button = gr.Button("🔄 Rafraîchir")
        
        with gr.Column(scale=2):
            # Détails du corpus
            gr.Markdown("### Détails du corpus")
            
            corpus_info = gr.HTML("Sélectionnez un corpus pour voir les détails")
            
            # Upload de documents
            gr.Markdown("### Ajouter des documents")
            
            file_upload = gr.File(
                label="Sélectionner des fichiers PDF",
                file_types=[".pdf"],
                file_count="multiple"
            )
            upload_button = gr.Button("Uploader", variant="primary")
            upload_status = gr.Textbox(label="Statut", interactive=False)
            
            # Liste des documents
            gr.Markdown("### Documents")
            
            documents_table = gr.Dataframe(
                headers=["ID", "Nom", "Type", "Date d'ajout", "Chunks", "Actions"],
                interactive=False,
                row_count=10,
                wrap=True
            )
            
            # Bouton de suppression pour le document sélectionné
            with gr.Row():
                document_id_input = gr.Number(
                    label="ID du document à supprimer",
                    precision=0
                )
                delete_document_button = gr.Button("Supprimer document", variant="stop")
                delete_status = gr.Textbox(
                    label="Statut",
                    interactive=False
                )
    
    # Chargement initial
    def on_load():
        state, corpus_id = load_corpus_list()
        
        # Préparer les choix pour le dropdown de corpus
        corpus_list = state.get("corpus_list", [])
        corpus_choices = [(c["name"], c["id"]) for c in corpus_list]
        
        # Préparer les détails du corpus et les documents
        if corpus_id:
            state_update, _ = load_corpus_details(corpus_id)
            state.update(state_update)
            
            corpus_details = state.get("current_corpus_details")
            if corpus_details:
                corpus_html = f"""
                <div class='corpus-details'>
                    <h3>{corpus_details['name']}</h3>
                    <p>{corpus_details.get('description', '')}</p>
                    <div class='corpus-stats'>
                        <span>Documents: {len(state.get("documents", []))}</span>
                        <span>Créé le: {format_timestamp(corpus_details.get('created_at', ''))}</span>
                    </div>
                </div>
                """
            else:
                corpus_html = "Sélectionnez un corpus pour voir les détails"
                
            # Mettre à jour le tableau des documents
            documents_data = []
            for doc in state.get("documents", []):
                documents_data.append([
                    doc["id"],
                    truncate_text(doc["filename"], 40),
                    doc["file_type"],
                    format_timestamp(doc.get("created_at", "")),
                    doc.get("chunk_count", 0),
                    f"🗑️ Supprimer"
                ])
        else:
            corpus_html = "Sélectionnez un corpus pour voir les détails"
            documents_data = []
        
        return [
            state,                     # rag_state
            corpus_id,                 # current_corpus_id
            corpus_choices,            # corpus_dropdown
            corpus_html,               # corpus_info
            documents_data             # documents_table
        ]
    
    # Événements
    create_corpus_button.click(
        fn=create_corpus,
        inputs=[corpus_name, corpus_description, rag_state],
        outputs=[create_status, rag_state, current_corpus_id]
    )
    
    # Mettre à jour les listes déroulantes lors du rafraîchissement
    def refresh_corpus_list():
        try:
            # Récupérer la liste mise à jour
            corpus_list = api_client.list_rag_corpus()
            
            # Mettre à jour l'état
            state = {
                "corpus_list": corpus_list,
                "current_corpus_id": corpus_list[0]["id"] if corpus_list else None,
                "error": None
            }
            
            # ID du corpus courant
            corpus_id = state["current_corpus_id"]
            
            # Préparer les choix pour le dropdown
            corpus_choices = [(c["name"], c["id"]) for c in corpus_list]
            
            # Charger les détails du corpus sélectionné
            if corpus_id:
                state_update, _ = load_corpus_details(corpus_id)
                state.update(state_update)
            
            corpus_details = state.get("current_corpus_details")
            if corpus_details:
                corpus_html = f"""
                <div class='corpus-details'>
                    <h3>{corpus_details['name']}</h3>
                    <p>{corpus_details.get('description', '')}</p>
                    <div class='corpus-stats'>
                        <span>Documents: {len(state.get("documents", []))}</span>
                        <span>Créé le: {format_timestamp(corpus_details.get('created_at', ''))}</span>
                    </div>
                </div>
                """
            else:
                corpus_html = "Sélectionnez un corpus pour voir les détails"
                
            # Mettre à jour le tableau des documents
            documents_data = []
            for doc in state.get("documents", []):
                documents_data.append([
                    doc["id"],
                    truncate_text(doc["filename"], 40),
                    doc["file_type"],
                    format_timestamp(doc.get("created_at", "")),
                    doc.get("chunk_count", 0),
                    f"🗑️ Supprimer"
                ])
            
            return state, corpus_id, corpus_choices, corpus_html, documents_data
        except Exception as e:
            logger.error(f"Erreur lors du rafraîchissement des corpus: {e}")
            return (
                {"corpus_list": [], "error": str(e)}, 
                None, 
                [],
                "Erreur lors du chargement des corpus",
                []
            )
    
    refresh_button.click(
        fn=refresh_corpus_list,
        outputs=[
            rag_state, 
            current_corpus_id, 
            corpus_dropdown,
            corpus_info,
            documents_table
        ]
    )
    
    # Sélection d'un corpus via le dropdown
    def select_corpus_by_id(corpus_id_or_tuple):
        # Gestion du cas où corpus_id pourrait être un tuple (nom, id)
        corpus_id = corpus_id_or_tuple
        if isinstance(corpus_id_or_tuple, (list, tuple)) and len(corpus_id_or_tuple) > 1:
            corpus_id = corpus_id_or_tuple[1]  # Extraire l'ID
            
        logger.info(f"Sélection du corpus {corpus_id}")
        if corpus_id is None:
            return None, {}, "Sélectionnez un corpus pour voir les détails", []
        
        try:
            # Charger les détails du corpus
            state_update, corpus_id = load_corpus_details(corpus_id)
            
            corpus_details = state_update.get("current_corpus_details")
            if corpus_details:
                corpus_html = f"""
                <div class='corpus-details'>
                    <h3>{corpus_details['name']}</h3>
                    <p>{corpus_details.get('description', '')}</p>
                    <div class='corpus-stats'>
                        <span>Documents: {len(state_update.get("documents", []))}</span>
                        <span>Créé le: {format_timestamp(corpus_details.get('created_at', ''))}</span>
                    </div>
                </div>
                """
            else:
                corpus_html = "Sélectionnez un corpus pour voir les détails"
                
            # Mettre à jour le tableau des documents
            documents_data = []
            for doc in state_update.get("documents", []):
                documents_data.append([
                    doc["id"],
                    truncate_text(doc["filename"], 40),
                    doc["file_type"],
                    format_timestamp(doc.get("created_at", "")),
                    doc.get("chunk_count", 0),
                    f"🗑️ Supprimer"
                ])
            
            return corpus_id, state_update, corpus_html, documents_data
        except Exception as e:
            logger.error(f"Erreur lors de la sélection du corpus {corpus_id}: {e}")
            return None, {}, "Erreur lors du chargement du corpus", []
    
    corpus_dropdown.change(
        fn=select_corpus_by_id,
        inputs=[corpus_dropdown],
        outputs=[current_corpus_id, rag_state, corpus_info, documents_table]
    )
    
    # Upload de documents
    upload_button.click(
        fn=upload_document,
        inputs=[file_upload, current_corpus_id],
        outputs=[upload_status, rag_state, current_corpus_id]
    )
    
    # Supprimer un document
    delete_document_button.click(
        fn=delete_document,
        inputs=[document_id_input, current_corpus_id],
        outputs=[delete_status, rag_state, current_corpus_id]
    )
    
    # Mettre à jour l'affichage quand l'état change
    def update_interface(state_dict):
        corpus_list = state_dict.get("corpus_list", [])
        current_id = state_dict.get("current_corpus_id")
        
        # Mise à jour du dropdown
        corpus_choices = [(c["name"], c["id"]) for c in corpus_list]
        
        corpus_details = state_dict.get("current_corpus_details")
        if corpus_details:
            corpus_html = f"""
            <div class='corpus-details'>
                <h3>{corpus_details['name']}</h3>
                <p>{corpus_details.get('description', '')}</p>
                <div class='corpus-stats'>
                    <span>Documents: {len(state_dict.get("documents", []))}</span>
                    <span>Créé le: {format_timestamp(corpus_details.get('created_at', ''))}</span>
                </div>
            </div>
            """
        else:
            corpus_html = "Sélectionnez un corpus pour voir les détails"
            
        # Mettre à jour le tableau des documents
        documents_data = []
        for doc in state_dict.get("documents", []):
            documents_data.append([
                doc["id"],
                truncate_text(doc["filename"], 40),
                doc["file_type"],
                format_timestamp(doc.get("created_at", "")),
                doc.get("chunk_count", 0),
                f"🗑️ Supprimer"
            ])
        
        return corpus_choices, corpus_html, documents_data
    
    rag_state.change(
        fn=update_interface,
        inputs=[rag_state],
        outputs=[corpus_dropdown, corpus_info, documents_table]
    )
    
    return {
        "rag_state": rag_state,
        "current_corpus_id": current_corpus_id,
        "corpus_dropdown": corpus_dropdown,
        "documents_table": documents_table,
        "corpus_info": corpus_info,
        "on_load": on_load,
        "on_load_outputs": [
            rag_state,
            current_corpus_id,
            corpus_dropdown,
            corpus_info,
            documents_table
        ]
    }