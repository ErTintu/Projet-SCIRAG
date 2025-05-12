from typing import List, Dict, Any
import html

def render_sources(sources: List[Dict[str, Any]]) -> str:
    """
    Génère le HTML pour afficher les sources utilisées dans une réponse.
    
    Args:
        sources: Liste des sources utilisées
    
    Returns:
        HTML pour afficher les sources
    """
    if not sources:
        return ""
    
    html_output = "<div class='sources-container'>"
    html_output += "<h3>🔍 Sources utilisées</h3>"
    html_output += "<div class='sources-list'>"
    
    for idx, source in enumerate(sources):
        source_type = source.get("source_type", "inconnu")
        source_id = source.get("source_id", "inconnu")
        chunk_text = source.get("chunk_text", "")
        score = source.get("score", 0)
        
        # Échapper le contenu HTML
        chunk_text = html.escape(chunk_text)
        
        # Limiter la longueur du texte affiché
        if len(chunk_text) > 200:
            chunk_text = chunk_text[:200] + "..."
        
        # Déterminer l'icône en fonction du type de source
        icon = "📄" if source_type == "document" else "📝"
        
        # Générer le HTML pour cette source
        html_output += f"""
        <div class='source-item'>
            <div class='source-header'>
                <span class='source-icon'>{icon}</span>
                <span class='source-type'>{source_type.capitalize()} #{source_id}</span>
                <span class='source-score'>Score: {score:.2f}</span>
            </div>
            <div class='source-content'>{chunk_text}</div>
        </div>
        """
    
    html_output += "</div></div>"
    
    return html_output