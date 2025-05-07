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
    
    # Fonction pour charger les corpus
    def load_corpus_list():
        try:
            corpus_list = api_client.list_rag_corpus()
            return {
                "corpus_list": corpus_list,
                "current_corpus_id": corpus_list[0]["id"] if corpus_list else None,
                "error": None
            }
        except Exception as e:
            logger.error(f"Erreur lors du chargement des corpus: {e}")
            return {
                "corpus_list": [],
                "current_corpus_id": None,
                "error": str(e)
            }
    
    # Fonction pour créer un nouveau corpus
    def create_corpus(name, description):
        if not name:
            return "Le nom ne peut pas être vide", rag_state.value
        
        try:
            new_corpus = api_client.create_rag_corpus(name, description)
            corpus_list = api_client.list_rag_corpus()
            
            return "Corpus créé avec succès", {
                "corpus_list": corpus_list,
                "current_corpus_id": new_corpus["id"],
                "current_corpus_details": new_corpus,
                "documents": [],
                "error": None
            }
        except Exception as e:
            logger.error(f"Erreur lors de la création du corpus: {e}")
            return f"Erreur: {str(e)}", rag_state.value
    
    # Fonction pour charger les détails d'un corpus
    def load_corpus_details(corpus_id):
        if not corpus_id:
            return {
                "current_corpus_id": None,
                "current_corpus_details": None,
                "documents": [],
                "error": None
            }
        
        try:
            corpus_details = api_client.get_rag_corpus(corpus_id)
            return {
                "current_corpus_id": corpus_id,
                "current_corpus_details": corpus_details,
                "documents": corpus_details.get("documents", []),
                "error": None
            }
        except Exception as e:
            logger.error(f"Erreur lors du chargement du corpus {corpus_id}: {e}")
            return {
                "error": str(e)
            }
    
    # Fonction pour uploader un document
    def upload_document(files, corpus_id):
        if not corpus_id:
            return "Veuillez d'abord sélectionner un corpus", None
        
        if not files:
            return "Aucun fichier sélectionné", None
        
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
        corpus_details = load_corpus_details(corpus_id)
        
        return "\n".join(results), corpus_details
    
    # Fonction pour supprimer un document
    def delete_document(document_id, corpus_id):
        if not corpus_id or not document_id:
            return "Veuillez sélectionner un corpus et un document", None
        
        try:
            result = api_client.delete_document(corpus_id, document_id)
            if result:
                message = f"Document {document_id} supprimé avec succès"
            else:
                message = f"Échec de la suppression du document {document_id}"
            
            # Recharger les détails du corpus
            corpus_details = load_corpus_details(corpus_id)
            
            return message, corpus_details
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du document {document_id}: {e}")
            return f"Erreur: {str(e)}", None
    
    # Interface
    with gr.Row():
        with gr.Column(scale=1):
            # Création d'un nouveau corpus
            with gr.Group(title="Créer un nouveau corpus"):
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
            with gr.Group(title="Corpus existants"):
                corpus_dropdown = gr.Dropdown(
                    label="Sélectionner un corpus",
                    choices=[],
                    value=None,
                    interactive=True
                )
                refresh_button = gr.Button("🔄 Rafraîchir")
        
        with gr.Column(scale=2):
            # Détails du corpus
            with gr.Group(title="Détails du corpus"):
                corpus_info = gr.HTML("Sélectionnez un corpus pour voir les détails")
            
            # Upload de documents
            with gr.Group(title="Ajouter des documents"):
                file_upload = gr.File(
                    label="Sélectionner des fichiers PDF",
                    file_types=[".pdf"],
                    file_count="multiple"
                )
                upload_button = gr.Button("Uploader", variant="primary")
                upload_status = gr.Textbox(label="Statut", interactive=False)
            
            # Liste des documents
            with gr.Group(title="Documents"):
                documents_table = gr.Dataframe(
                    headers=["ID", "Nom", "Type", "Date d'ajout", "Chunks", "Actions"],
                    interactive=False,
                    height=300
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
        state = load_corpus_list()
        
        # Mettre à jour la liste des corpus
        corpus_list = state.get("corpus_list", [])
        corpus_choices = [(c["name"], c["id"]) for c in corpus_list]
        current_id = state.get("current_corpus_id")
        
        # Mettre à jour l'affichage d'erreur
        error = state.get("error")
        error_message = f"Erreur: {error}" if error else ""
        
        return [
            state,  # rag_state
            gr.Dropdown(choices=corpus_choices, value=current_id),  # corpus_dropdown
            error_message  # create_status
        ]
    
    gr.on(
        gr.triggers.Loads,
        fn=on_load,
        outputs=[
            rag_state,
            corpus_dropdown,
            create_status
        ]
    )
    
    # Événements
    create_corpus_button.click(
        fn=create_corpus,
        inputs=[corpus_name, corpus_description],
        outputs=[create_status, rag_state]
    )
    
    refresh_button.click(
        fn=load_corpus_list,
        outputs=[rag_state]
    )
    
    # Charger les détails d'un corpus lorsqu'il est sélectionné
    def handle_corpus_selection(corpus_id):
        updates = load_corpus_details(corpus_id)
        corpus_details = updates.get("current_corpus_details")
        documents = updates.get("documents", [])
        
        # Mettre à jour l'affichage des détails du corpus
        if corpus_details:
            html = f"""
            <div class='corpus-details'>
                <h3>{corpus_details['name']}</h3>
                <p>{corpus_details.get('description', '')}</p>
                <div class='corpus-stats'>
                    <span>Documents: {len(documents)}</span>
                    <span>Créé le: {format_timestamp(corpus_details.get('created_at', ''))}</span>
                </div>
            </div>
            """
        else:
            html = "Sélectionnez un corpus pour voir les détails"
        
        # Mettre à jour le tableau des documents
        table_data = []
        for doc in documents:
            table_data.append([
                doc["id"],
                truncate_text(doc["filename"], 40),
                doc["file_type"],
                format_timestamp(doc.get("created_at", "")),
                doc.get("chunk_count", 0),
                f"🗑️ Supprimer"  # Action (non fonctionnelle ici, juste pour l'affichage)
            ])
        
        return [
            updates,  # rag_state
            html,  # corpus_info
            table_data,  # documents_table
        ]
    
    corpus_dropdown.change(
        fn=handle_corpus_selection,
        inputs=[corpus_dropdown],
        outputs=[
            rag_state,
            corpus_info,
            documents_table
        ]
    )
    
    # Upload de documents
    upload_button.click(
        fn=upload_document,
        inputs=[file_upload, rag_state["current_corpus_id"]],
        outputs=[upload_status, rag_state]
    )
    
    # Supprimer un document
    delete_document_button.click(
        fn=delete_document,
        inputs=[document_id_input, rag_state["current_corpus_id"]],
        outputs=[delete_status, rag_state]
    )
    
    # Surveillance de l'état pour mettre à jour l'interface
    def update_corpus_dropdown(state):
        corpus_list = state.get("corpus_list", [])
        return gr.Dropdown(
            choices=[(c["name"], c["id"]) for c in corpus_list],
            value=state.get("current_corpus_id")
        )
    
    def update_documents_table(state):
        documents = state.get("documents", [])
        
        table_data = []
        for doc in documents:
            table_data.append([
                doc["id"],
                truncate_text(doc["filename"], 40),
                doc["file_type"],
                format_timestamp(doc.get("created_at", "")),
                doc.get("chunk_count", 0),
                f"🗑️ Supprimer"  # Action (non fonctionnelle ici, juste pour l'affichage)
            ])
        
        return table_data
    
    def update_corpus_info(state):
        details = state.get("current_corpus_details")
        documents = state.get("documents", [])
        
        if not details:
            return "Sélectionnez un corpus pour voir les détails"
        
        html = f"""
        <div class='corpus-details'>
            <h3>{details['name']}</h3>
            <p>{details.get('description', '')}</p>
            <div class='corpus-stats'>
                <span>Documents: {len(documents)}</span>
                <span>Créé le: {format_timestamp(details.get('created_at', ''))}</span>
            </div>
        </div>
        """
        
        return html
    
    # Mise à jour de l'interface en fonction de l'état
    rag_state.change(
        fn=update_corpus_dropdown,
        inputs=[rag_state],
        outputs=[corpus_dropdown]
    )
    
    rag_state.change(
        fn=update_documents_table,
        inputs=[rag_state],
        outputs=[documents_table]
    )
    
    rag_state.change(
        fn=update_corpus_info,
        inputs=[rag_state],
        outputs=[corpus_info]
    )
    
    return {
        "rag_state": rag_state,
        "corpus_dropdown": corpus_dropdown,
        "documents_table": documents_table,
        "corpus_info": corpus_info
    }