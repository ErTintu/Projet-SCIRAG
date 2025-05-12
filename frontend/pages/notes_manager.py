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
    
    # État pour stocker l'ID de la note courante
    current_note_id = gr.State(None)
    
    # Fonction pour charger les notes
    def load_notes_list():
        try:
            notes_list = api_client.list_notes()
            return {
                "notes_list": notes_list,
                "current_note_id": notes_list[0]["id"] if notes_list else None,
                "error": None
            }, notes_list[0]["id"] if notes_list else None
        except Exception as e:
            logger.error(f"Erreur lors du chargement des notes: {e}")
            return {
                "notes_list": [],
                "current_note_id": None,
                "error": str(e)
            }, None
    
    # Fonction pour créer une nouvelle note
    def create_note(title, content, state_value):
        if not title:
            return "Le titre est obligatoire", state_value, None
        
        try:
            new_note = api_client.create_note(title, content)
            notes_list = api_client.list_notes()
            
            return "Note créée avec succès", {
                "notes_list": notes_list,
                "current_note_id": new_note["id"],
                "current_note_details": new_note,
                "error": None
            }, new_note["id"]
        except Exception as e:
            logger.error(f"Erreur lors de la création de la note: {e}")
            return f"Erreur: {str(e)}", state_value, None
    
    # Fonction pour mettre à jour une note existante
    def update_note(note_id, title, content, state_value):
        if not note_id:
            return "Aucune note sélectionnée", state_value, None
        
        if not title:
            return "Le titre est obligatoire", state_value, None
        
        try:
            updated_note = api_client.update_note(note_id, title, content)
            notes_list = api_client.list_notes()
            
            return "Note mise à jour avec succès", {
                "notes_list": notes_list,
                "current_note_id": note_id,
                "current_note_details": updated_note,
                "error": None
            }, note_id
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la note {note_id}: {e}")
            return f"Erreur: {str(e)}", state_value, None
    
    # Fonction pour charger les détails d'une note
    def load_note_details(note_id):
        if not note_id:
            return {
                "current_note_id": None,
                "current_note_details": None,
                "error": None
            }, None
        
        try:
            note = api_client.get_note(note_id)
            
            return {
                "current_note_id": note_id,
                "current_note_details": note,
                "error": None
            }, note_id
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la note {note_id}: {e}")
            return {
                "error": str(e)
            }, None
    
    # Fonction pour supprimer une note
    def delete_note(note_id, state_value):
        if not note_id:
            return "Aucune note sélectionnée", state_value, None
        
        try:
            success = api_client.delete_note(note_id)
            if not success:
                return "Échec de la suppression de la note", state_value, None
            
            notes_list = api_client.list_notes()
            
            return "Note supprimée avec succès", {
                "notes_list": notes_list,
                "current_note_id": notes_list[0]["id"] if notes_list else None,
                "current_note_details": None,
                "error": None
            }, notes_list[0]["id"] if notes_list else None
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la note {note_id}: {e}")
            return f"Erreur: {str(e)}", state_value, None
    
    # Interface
    with gr.Row():
        with gr.Column(scale=1):
            # Liste des notes existantes
            gr.Markdown("### Notes existantes")
            
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
            gr.Markdown("### Infos vectorisation")
            
            note_stats = gr.HTML()
        
        with gr.Column(scale=2):
            # Création/édition de note
            gr.Markdown("### Créer ou modifier une note")
            
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
        """Fonction de chargement pour notes_manager.py"""
        state, note_id = load_notes_list()
        return state, note_id
    
    # Événements
    create_note_button.click(
        fn=create_note,
        inputs=[note_title, note_content, notes_state],
        outputs=[status_message, notes_state, current_note_id]
    )
    
    update_note_button.click(
        fn=update_note,
        inputs=[current_note_id, note_title, note_content, notes_state],
        outputs=[status_message, notes_state, current_note_id]
    )
    
    refresh_button.click(
        fn=load_notes_list,
        outputs=[notes_state, current_note_id]
    )
    
    # Chargement d'une note lorsqu'elle est sélectionnée
    def handle_note_selection(note_id):
        updates, note_id_updated = load_note_details(note_id)
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
            note_id_updated,  # current_note_id
            title,  # note_title
            content,  # note_content
            html,  # note_stats
        ]
    
    notes_dropdown.change(
        fn=handle_note_selection,
        inputs=[notes_dropdown],
        outputs=[
            notes_state,
            current_note_id,
            note_title,
            note_content,
            note_stats
        ]
    )
    
    # Supprimer une note
    delete_button.click(
        fn=lambda note_id, state: delete_note(note_id, state),
        inputs=[current_note_id, notes_state],
        outputs=[status_message, notes_state, current_note_id]
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
        "current_note_id": current_note_id,
        "notes_dropdown": notes_dropdown,
        "note_title": note_title,
        "note_content": note_content,
        "on_load": on_load
    }