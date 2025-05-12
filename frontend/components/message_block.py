import gradio as gr
from typing import Dict, Any, List
import html

def render_message(message: Dict[str, Any], avatar=True) -> List:
    """
    Rendu personnalisé pour les messages dans le chatbot.
    
    Args:
        message: Dictionnaire contenant les informations du message
        avatar: Afficher les avatars ou non
    
    Returns:
        Liste [author_avatar, message_content] pour Gradio Chatbot
    """
    if not isinstance(message, dict):
        # Si ce n'est pas un dictionnaire, retourner tel quel
        return [None, str(message)]
    
    role = message.get("role", "")
    content = message.get("content", "")
    
    # Échapper le contenu HTML
    if isinstance(content, str):
        content = html.escape(content)
    else:
        content = str(content)
    
    # Avatars selon le rôle
    if role == "user":
        avatar_img = "👤"  # Avatar utilisateur
    elif role == "assistant":
        avatar_img = "🧠"  # Avatar assistant
    elif role == "system":
        avatar_img = "ℹ️"  # Avatar système
    else:
        avatar_img = "❓"  # Avatar par défaut
    
    # Si le message est en chargement, ajouter une animation
    if message.get("is_loading"):
        content = f"<div class='loading-spinner'>{content}</div>"
    
    # Formatage du contenu selon le rôle
    if role == "user":
        content = f"<div class='user-message'>{content}</div>"
    elif role == "assistant":
        content = f"<div class='assistant-message'>{content}</div>"
    elif role == "system":
        content = f"<div class='system-message'>{content}</div>"
    
    # Si le message a des sources, ajouter un indicateur
    if message.get("sources"):
        content += "\n\n<small>🔍 Ce message contient des sources</small>"
    
    return [avatar_img, content]