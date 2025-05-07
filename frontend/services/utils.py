import time
import re
from typing import Dict, List, Any, Optional

def format_timestamp(timestamp: str) -> str:
    """
    Formate un horodatage ISO en format lisible.
    
    Args:
        timestamp: Horodatage au format ISO
        
    Returns:
        Chaîne formatée (ex: "23 mai 2024, 14:30")
    """
    if not timestamp:
        return ""
    
    try:
        # Conversion de l'ISO timestamp
        from datetime import datetime
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        
        # Format français
        return dt.strftime("%d %b %Y, %H:%M")
    except Exception:
        return timestamp

def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Tronque le texte à une longueur maximale.
    
    Args:
        text: Texte à tronquer
        max_length: Longueur maximale
        
    Returns:
        Texte tronqué avec "..." si nécessaire
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length] + "..."

def sanitize_filename(filename: str) -> str:
    """
    Sanitize un nom de fichier en supprimant les caractères invalides.
    
    Args:
        filename: Nom de fichier à sanitizer
        
    Returns:
        Nom de fichier valide
    """
    # Supprimer les caractères spéciaux et les remplacer par '_'
    sanitized = re.sub(r'[\\/*?:"<>|]', '_', filename)
    return sanitized