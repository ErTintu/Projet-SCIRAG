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
            logger.info(f"Corpus chargés: {len(corpus_list)}")
            
            # Sélectionner le premier corpus comme corpus courant
            current_id = corpus_list[0]["id"] if corpus_list else None
            
            # Préparer les choix pour le dropdown
            choices = [(c["name"], c["id"]) for c in corpus_list]
            
            return {
                "corpus_list": corpus_list,
                "current_corpus_id": current_id,
                "error": None
            }, current_id, choices
        except Exception as e:
            logger.error(f"Erreur lors du chargement des corpus: {e}")
            return {
                "corpus_list": [],
                "current_corpus_id": None,
                "error": str(e)
            }, None, []
    
    # Fonction pour créer un nouveau corpus
    def create_corpus(name, description):
        if not name:
            return "Le nom ne peut pas être vide", [], None, None
        
        try:
            new_corpus = api_client.create_rag_corpus(name, description)
            corpus_list = api_client.list_rag_corpus()
            choices = [(c["name"], c["id"]) for c in corpus_list]
            
            new_state = {
                "corpus_list": corpus_list,
                "current_corpus_id": new_corpus["id"],
                "current_corpus_details": new_corpus,
                "documents": [],
                "error": None
            }
            
            return "Corpus créé avec succès", choices, new_state, new_corpus["id"]
        except Exception as e:
            logger.error(f"Erreur lors de la création du corpus: {e}")
            return f"Erreur: {str(e)}", [], None, None
    
    # Fonction pour charger les détails d'un corpus
    def load_corpus_details(corpus_id):
        if not corpus_id:
            return {
                "current_corpus_id": None,
                "current_corpus_details": None,
                "documents": [],
                "error": None
            }, None, "Aucun corpus sélectionné", []
        
        try:
            # Si corpus_id est une chaîne ou un tuple (nom, id), essayer de l'extraire
            if isinstance(corpus_id, (list, tuple)) and len(corpus_id) > 1:
                corpus_id = corpus_id[1]  # Extraire l'ID du tuple (nom, id)
            
            logger.info(f"Chargement du corpus {corpus_id}")
            corpus_details = api_client.get_rag_corpus(corpus_id)
            
            # Générer le HTML pour afficher les détails du corpus
            corpus_html = f"""
            <div class='corpus-details'>
                <h3>{corpus_details['name']}</h3>
                <p>{corpus_details.get('description', '')}</p>
                <div class='corpus-stats'>
                    <p><strong>Documents:</strong> {len(corpus_details.get("documents", []))}</p>
                    <p><strong>Créé le:</strong> {format_timestamp(corpus_details.get('created_at', ''))}</p>
                    <p><strong>Modifié le:</strong> {format_timestamp(corpus_details.get('updated_at', ''))}</p>
                </div>
            </div>
            """
            
            # Préparer les données des documents pour le tableau
            documents_data = []
            for doc in corpus_details.get("documents", []):
                documents_data.append([
                    doc["id"],
                    truncate_text(doc["filename"], 40),
                    doc["file_type"],
                    format_timestamp(doc.get("created_at", "")),
                    doc.get("chunk_count", 0)
                ])
            
            return {
                "current_corpus_id": corpus_id,
                "current_corpus_details": corpus_details,
                "documents": corpus_details.get("documents", []),
                "error": None
            }, corpus_id, corpus_html, documents_data
        except Exception as e:
            logger.error(f"Erreur lors du chargement du corpus {corpus_id}: {e}")
            return {
                "error": str(e)
            }, None, f"Erreur: {str(e)}", []
    
    # Fonction pour supprimer un corpus
    def delete_corpus(corpus_id):
        if not corpus_id:
            return "Aucun corpus sélectionné", [], None, None
        
        try:
            result = api_client.delete_rag_corpus(corpus_id)
            
            # Recharger la liste des corpus après suppression
            corpus_list = api_client.list_rag_corpus()
            choices = [(c["name"], c["id"]) for c in corpus_list]
            current_id = corpus_list[0]["id"] if corpus_list else None
            
            new_state = {
                "corpus_list": corpus_list,
                "current_corpus_id": current_id,
                "current_corpus_details": None,
                "documents": [],
                "error": None
            }
            
            return "Corpus supprimé avec succès", choices, new_state, current_id
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du corpus {corpus_id}: {e}")
            return f"Erreur: {str(e)}", [], None, None
    
    # Fonction pour uploader un document
    def upload_document(files, corpus_id):
        if not corpus_id:
            return "Veuillez d'abord sélectionner un corpus"
        
        if not files:
            return "Aucun fichier sélectionné"
        
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
        
        # Recharger les détails du corpus et renvoyer seulement le message de statut
        return "\n".join(results)
    
    # Fonction pour supprimer un document
    def delete_document(document_id, corpus_id):
        if not corpus_id or not document_id:
            return "Veuillez sélectionner un corpus et un document"
        
        try:
            result = api_client.delete_document(corpus_id, document_id)
            
            if result:
                message = f"Document {document_id} supprimé avec succès"
            else:
                message = f"Échec de la suppression du document {document_id}"
            
            return message
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du document {document_id}: {e}")
            return f"Erreur: {str(e)}"
    
    # Interface
    with gr.Row():
        with gr.Column(scale=1):
            # Liste des corpus existants
            gr.Markdown("### Corpus RAG existants")
            
            corpus_dropdown = gr.Dropdown(
                label="Sélectionner un corpus",
                choices=[],
                value=None,
                interactive=True,
                allow_custom_value=True
            )
            
            new_corpus_name = gr.Textbox(
                label="Nom du nouveau corpus",
                placeholder="Mon nouveau corpus RAG"
            )
            
            new_corpus_description = gr.Textbox(
                label="Description (optionnelle)",
                placeholder="Description du corpus...",
                lines=2
            )
            
            create_corpus_button = gr.Button("Créer corpus", variant="primary")
            
            with gr.Row():
                refresh_corpus_button = gr.Button("🔄 Rafraîchir")
                delete_corpus_button = gr.Button("🗑️ Supprimer", variant="stop")
            
            # Message de statut
            corpus_status = gr.Textbox(
                label="Statut",
                interactive=False
            )
        
        with gr.Column(scale=2):
            # Détails du corpus et documents
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
            upload_status = gr.Textbox(label="Statut de l'upload", interactive=False)
            
            # Liste des documents
            gr.Markdown("### Documents du corpus")
            
            documents_table = gr.Dataframe(
                headers=["ID", "Nom", "Type", "Date d'ajout", "Chunks"],
                interactive=False,
                row_count=10,
                wrap=True
            )
            
            # Suppression de document
            with gr.Row():
                document_id_input = gr.Number(
                    label="ID du document à supprimer",
                    precision=0
                )
                delete_document_button = gr.Button("Supprimer document", variant="stop")
                delete_status = gr.Textbox(
                    label="Statut de suppression",
                    interactive=False
                )
    
    # Chargement initial
   # Chargement initial
    def on_load():
        """Fonction de chargement initiale"""
        try:
            # Charger la liste des corpus depuis l'API
            corpus_list = api_client.list_rag_corpus()
            logger.info(f"Corpus chargés au démarrage: {len(corpus_list)}")
            
            # Préparer les choix pour le dropdown
            corpus_choices = [(c["name"], c["id"]) for c in corpus_list]
            
            # Sélectionner le premier corpus comme corpus courant
            current_id = corpus_list[0]["id"] if corpus_list else None
            
            # Mettre à jour l'état
            state = {
                "corpus_list": corpus_list,
                "current_corpus_id": current_id,
                "current_corpus_details": None,
                "documents": [],
                "error": None
            }
            
            # Si nous avons un corpus sélectionné, chargez ses détails
            corpus_html = "Sélectionnez un corpus pour voir les détails"
            documents_data = []
            
            if current_id:
                try:
                    corpus_details = api_client.get_rag_corpus(current_id)
                    state["current_corpus_details"] = corpus_details
                    state["documents"] = corpus_details.get("documents", [])
                    
                    # Générer le HTML des détails
                    corpus_html = f"""
                    <div class='corpus-details'>
                        <h3>{corpus_details['name']}</h3>
                        <p>{corpus_details.get('description', '')}</p>
                        <div class='corpus-stats'>
                            <p><strong>Documents:</strong> {len(corpus_details.get("documents", []))}</p>
                            <p><strong>Créé le:</strong> {format_timestamp(corpus_details.get('created_at', ''))}</p>
                            <p><strong>Modifié le:</strong> {format_timestamp(corpus_details.get('updated_at', ''))}</p>
                        </div>
                    </div>
                    """
                    
                    # Préparer le tableau des documents
                    for doc in corpus_details.get("documents", []):
                        documents_data.append([
                            doc["id"],
                            truncate_text(doc["filename"], 40),
                            doc["file_type"],
                            format_timestamp(doc.get("created_at", "")),
                            doc.get("chunk_count", 0)
                        ])
                except Exception as e:
                    logger.error(f"Erreur lors du chargement du corpus {current_id}: {e}")
                    corpus_html = f"Erreur de chargement: {str(e)}"
            
            # Créer explicitement un nouveau dropdown pour s'assurer que les choix sont correctement formatés
            dropdown = gr.Dropdown(
                label="Sélectionner un corpus",
                choices=corpus_choices,
                value=current_id if current_id else None,
                interactive=True,
                allow_custom_value=True
            )
            
            return state, current_id, dropdown, corpus_html, documents_data
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement initial: {e}")
            return {
                "corpus_list": [],
                "current_corpus_id": None,
                "error": str(e)
            }, None, gr.Dropdown(choices=[], label="Sélectionner un corpus"), "Erreur de chargement", []
    
    # Attachement des événements
    # 1. Créer un corpus
    create_corpus_button.click(
        fn=create_corpus,
        inputs=[new_corpus_name, new_corpus_description],
        outputs=[corpus_status, corpus_dropdown, rag_state, current_corpus_id]
    )
    
    # 2. Rafraîchir la liste des corpus
    def refresh_corpus_list_fn():
        """Fonction pour rafraîchir la liste des corpus"""
        try:
            corpus_list = api_client.list_rag_corpus()
            choices = [(c["name"], c["id"]) for c in corpus_list]
            return choices
        except Exception as e:
            logger.error(f"Erreur lors du rafraîchissement des corpus: {e}")
            return []

    # Rafraîchir la liste des corpus
    refresh_corpus_button.click(
        fn=refresh_corpus_list_fn,
        outputs=[corpus_dropdown]
    )
    # 3. Supprimer un corpus
    delete_corpus_button.click(
        fn=delete_corpus,
        inputs=[current_corpus_id],
        outputs=[corpus_status, corpus_dropdown, rag_state, current_corpus_id]
    )
    
    # 4. Sélectionner un corpus
    def on_corpus_selected(corpus_value):
        """Quand un corpus est sélectionné dans le dropdown"""
        if corpus_value is None:
            return None, "Aucun corpus sélectionné", []
            
        # Extraire l'ID si c'est un tuple (nom, id)
        corpus_id = corpus_value
        if isinstance(corpus_value, (list, tuple)) and len(corpus_value) > 1:
            corpus_id = corpus_value[1]
        
        # Charger les détails du corpus et mettre à jour l'interface
        try:
            corpus_update, corpus_id, corpus_html, documents_data = load_corpus_details(corpus_id)
            return corpus_id, corpus_html, documents_data
        except Exception as e:
            logger.error(f"Erreur lors de la sélection du corpus: {e}")
            return None, f"Erreur: {str(e)}", []
    
    corpus_dropdown.change(
        fn=on_corpus_selected,
        inputs=[corpus_dropdown],
        outputs=[current_corpus_id, corpus_info, documents_table]
    )
    
    # 5. Upload de documents
    upload_button.click(
        fn=upload_document,
        inputs=[file_upload, current_corpus_id],
        outputs=[upload_status]
    ).then(
        # Après upload, rafraîchir les détails du corpus
        fn=on_corpus_selected,
        inputs=[current_corpus_id],
        outputs=[current_corpus_id, corpus_info, documents_table]
    )
    
    # 6. Suppression d'un document
    delete_document_button.click(
        fn=delete_document,
        inputs=[document_id_input, current_corpus_id],
        outputs=[delete_status]
    ).then(
        # Après suppression, rafraîchir les détails du corpus
        fn=on_corpus_selected,
        inputs=[current_corpus_id],
        outputs=[current_corpus_id, corpus_info, documents_table]
    )
    
    # Styles CSS
    gr.HTML("""
    <style>
    .corpus-details {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 20px;
    }
    
    .corpus-details h3 {
        margin-top: 0;
        color: #343a40;
        border-bottom: 1px solid #dee2e6;
        padding-bottom: 10px;
    }
    
    .corpus-stats {
        display: flex;
        flex-wrap: wrap;
        gap: 15px;
        margin-top: 10px;
    }
    
    .corpus-stats p {
        margin: 0;
        background-color: #e9ecef;
        padding: 5px 10px;
        border-radius: 4px;
        font-size: 0.9em;
    }
    </style>
    """)
    
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