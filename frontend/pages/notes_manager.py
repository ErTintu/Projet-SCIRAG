import gradio as gr
import logging
from typing import List, Dict, Any
from services.utils import format_timestamp, truncate_text

logger = logging.getLogger(__name__)

def create_notes_manager(api_client):
    """
    Crée l'interface de gestion des notes personnelles.
    
    Args:
        api_client: Instance du client API
        
    Returns:
        Dict contenant les composants de l'interface
    """
    # État des notes
    notes_state = gr.State({
        "notes_list": [],
        "current_note_id": None,
        "current_note_details": None,
        "error": None
    })
    
    # Fonction pour charger les notes
    def load_notes_list():
        try:
            notes_list = api_client.list_notes()
            return {
                "notes_list": notes_list,
                "current_note_id": notes_list[0]["id"] if notes_list else None,
                "error": None
            }
        except Exception as e:
            logger.error(f"Erreur lors du chargement des notes: {e}")
            return {
                "notes_list": [],
                "current_note_id": None,
                "error": str(e)
            }
    
    # Fonction pour créer une nouvelle note
    def create_note(title, content):
        if not title:
            return "Le titre est obligatoire", notes_state.value
        
        try:
            new_note = api_client.create_note(title, content)
            notes_list = api_client.list_notes()
            
            return "Note créée avec succès", {
                "notes_list": notes_list,
                "current_note_id": new_note["id"],
                "current_note_details": new_note,
                "error": None
            }
        except Exception as e:
            logger.error(f"Erreur lors de la création de la note: {e}")
            return f"Erreur: {str(e)}", notes_state.value
    
    # Fonction pour mettre à jour une note existante
    def update_note(note_id, title, content):
        if not note_id:
            return "Aucune note sélectionnée", notes_state.value
        
        if not title:
            return "Le titre est obligatoire", notes_state.value
        
        try:
            updated_note = api_client.update_note(note_id, title, content)
            notes_list = api_client.list_notes()
            
            return "Note mise à jour avec succès", {
                "notes_list": notes_list,
                "current_note_id": note_id,
                "current_note_details": updated_note,
                "error": None
            }
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la note {note_id}: {e}")
            return f"Erreur: {str(e)}", notes_state.value
    
    # Fonction pour charger les détails d'une note
    def load_note_details(note_id):
        if not note_id:
            return {
                "current_note_id": None,
                "current_note_details": None,
                "error": None
            }
        
        try:
            note = api_client.get_note(note_id)
            
            return {
                "current_note_id": note_id,
                "current_note_details": note,
                "error": None
            }
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la note {note_id}: {e}")
            return {
                "error": str(e)
            }
    
    # Fonction pour supprimer une note
    def delete_note(note_id):
        if not note_id:
            return "Aucune note sélectionnée", notes_state.value
        
        try:
            success = api_client.delete_note(note_id)
            if not success:
                return "Échec de la suppression de la note", notes_state.value
            
            notes_list = api_client.list_notes()
            
            return "Note supprimée avec succès", {
                "notes_list": notes_list,
                "current_note_id": notes_list[0]["id"] if notes_list else None,
                "current_note_details": None,
                "error": None
            }
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la note {note_id}: {e}")
            return f"Erreur: {str(e)}", notes_state.value
    
# Interface
with gr.Row():
    with gr.Column(scale=1):
        # Liste des notes existantes
        with gr.Group(title="Notes existantes"):
            notes_dropdown = gr.Dropdown(
                label="Sélectionner une note",
                choices=[],
                value=None,
                interactive=True
            )
            
            with gr.Row():
                refresh_button = gr.Button("🔄 Rafraîchir")
                delete_button = gr.Button("🗑️ Supprimer", variant="stop")
        
        # Informations sur la vectorisation
        with gr.Group(title="Infos vectorisation"):
            note_stats = gr.HTML()
    
    with gr.Column(scale=2):  # <-- Ici, bien indenté pour ouvrir la colonne
        # Création/édition de note
        with gr.Group(title="Créer ou modifier une note"):
            note_title = gr.Textbox(label="Titre")
            note_content = gr.Textbox(
                label="Contenu",
                lines=10,
                placeholder="Contenu de la note..."
            )
            
            with gr.Row():
                create_note_button = gr.Button("Créer", variant="primary")
                update_note_button = gr.Button("Mettre à jour", variant="secondary")
            
            status_message = gr.Textbox(
                label="Statut",
                interactive=False
            )
    
    # Chargement initial
    def on_load():
        state = load_notes_list()
        
        # Mettre à jour la liste des notes
        notes_list = state.get("notes_list", [])
        note_choices = [(n["title"], n["id"]) for n in notes_list]
        current_id = state.get("current_note_id")
        
        # Mettre à jour l'affichage d'erreur
        error = state.get("error")
        error_message = f"Erreur: {error}" if error else ""
        
        return [
            state,  # notes_state
            gr.Dropdown(choices=note_choices, value=current_id),  # notes_dropdown
            error_message  # status_message
        ]
    
    gr.on(
        gr.triggers.Loads,
        fn=on_load,
        outputs=[
            notes_state,
            notes_dropdown,
            status_message
        ]
    )
    
    # Événements
    create_note_button.click(
        fn=create_note,
        inputs=[note_title, note_content],
        outputs=[status_message, notes_state]
    )
    
    update_note_button.click(
        fn=update_note,
        inputs=[notes_state["current_note_id"], note_title, note_content],
        outputs=[status_message, notes_state]
    )
    
    refresh_button.click(
        fn=load_notes_list,
        outputs=[notes_state]
    )
    
    # Chargement d'une note lorsqu'elle est sélectionnée
    def handle_note_selection(note_id):
        updates = load_note_details(note_id)
        note_details = updates.get("current_note_details")
        
        # Mettre à jour les champs de titre et contenu
        title = note_details.get("title", "") if note_details else ""
        content = note_details.get("content", "") if note_details else ""
        
        # Mettre à jour les statistiques de la note
        if note_details:
            html = f"""
            <div class='note-stats'>
                <p><strong>ID:</strong> {note_details['id']}</p>
                <p><strong>Créée le:</strong> {format_timestamp(note_details.get('created_at', ''))}</p>
                <p><strong>Modifiée le:</strong> {format_timestamp(note_details.get('updated_at', ''))}</p>
                <p><strong>Chunks:</strong> {note_details.get('chunk_count', 0)}</p>
            </div>
            """
        else:
            html = "Sélectionnez une note pour voir les détails"
        
        return [
            updates,  # notes_state
            title,  # note_title
            content,  # note_content
            html,  # note_stats
        ]
    
    notes_dropdown.change(
        fn=handle_note_selection,
        inputs=[notes_dropdown],
        outputs=[
            notes_state,
            note_title,
            note_content,
            note_stats
        ]
    )
    
    # Supprimer une note
    delete_button.click(
        fn=lambda state: delete_note(state.get("current_note_id")),
        inputs=[notes_state],
        outputs=[status_message, notes_state]
    )
    
    # Surveillance de l'état pour mettre à jour l'interface
    def update_notes_dropdown(state):
        notes_list = state.get("notes_list", [])
        return gr.Dropdown(
            choices=[(n["title"], n["id"]) for n in notes_list],
            value=state.get("current_note_id")
        )
    
    def update_note_stats(state):
        details = state.get("current_note_details")
        
        if not details:
            return "Sélectionnez une note pour voir les détails"
        
        html = f"""
        <div class='note-stats'>
            <p><strong>ID:</strong> {details['id']}</p>
            <p><strong>Créée le:</strong> {format_timestamp(details.get('created_at', ''))}</p>
            <p><strong>Modifiée le:</strong> {format_timestamp(details.get('updated_at', ''))}</p>
            <p><strong>Chunks:</strong> {details.get('chunk_count', 0)}</p>
        </div>
        """
        
        return html
    
    # Mise à jour de l'interface en fonction de l'état
    notes_state.change(
        fn=update_notes_dropdown,
        inputs=[notes_state],
        outputs=[notes_dropdown]
    )
    
    notes_state.change(
        fn=update_note_stats,
        inputs=[notes_state],
        outputs=[note_stats]
    )
    
    return {
        "notes_state": notes_state,
        "notes_dropdown": notes_dropdown,
        "note_title": note_title,
        "note_content": note_content
    }