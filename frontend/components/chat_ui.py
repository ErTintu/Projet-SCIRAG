"""
Chat UI Component for SCIRAG.
This module provides the UI for chat interactions.
"""

import streamlit as st
from typing import List, Dict, Any, Optional, Callable, Tuple
import time
from datetime import datetime
import re

def format_time(timestamp_str: str) -> str:
    """Format ISO timestamp to a readable time."""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime("%H:%M:%S")
    except:
        return ""

def highlight_sources(text: str, sources: List[Dict[str, Any]]) -> str:
    """Highlight text mentions from sources with colors."""
    if not sources:
        return text
    
    # Create a copy of the text
    highlighted_text = text
    
    # Process each source
    for source in sources:
        source_type = source.get("source_type")
        source_id = source.get("source_id")
        
        if not source_type or not source_id:
            continue
        
        # Highlight based on source type
        if source_type == "document":
            # Find likely quotes or references to documents
            doc_patterns = [
                (r'"([^"]{10,})"', r'<span style="background-color: #E3F2FD; border-radius: 3px; padding: 0 3px;">\1</span>'),  # Quoted text
                (r'«([^»]{10,})»', r'<span style="background-color: #E3F2FD; border-radius: 3px; padding: 0 3px;">\1</span>'),  # French quotes
                (r'selon le document', r'<span style="background-color: #E3F2FD; border-radius: 3px; padding: 0 3px;">selon le document</span>'),
                (r'd\'après le document', r'<span style="background-color: #E3F2FD; border-radius: 3px; padding: 0 3px;">d\'après le document</span>'),
                (r'dans le document', r'<span style="background-color: #E3F2FD; border-radius: 3px; padding: 0 3px;">dans le document</span>'),
                (r'le document mentionne', r'<span style="background-color: #E3F2FD; border-radius: 3px; padding: 0 3px;">le document mentionne</span>')
            ]
            
            for pattern, replacement in doc_patterns:
                highlighted_text = re.sub(pattern, replacement, highlighted_text)
                
        elif source_type == "note":
            # Find likely references to notes
            note_patterns = [
                (r'selon la note', r'<span style="background-color: #FFF8E1; border-radius: 3px; padding: 0 3px;">selon la note</span>'),
                (r'd\'après la note', r'<span style="background-color: #FFF8E1; border-radius: 3px; padding: 0 3px;">d\'après la note</span>'),
                (r'dans la note', r'<span style="background-color: #FFF8E1; border-radius: 3px; padding: 0 3px;">dans la note</span>'),
                (r'la note mentionne', r'<span style="background-color: #FFF8E1; border-radius: 3px; padding: 0 3px;">la note mentionne</span>')
            ]
            
            for pattern, replacement in note_patterns:
                highlighted_text = re.sub(pattern, replacement, highlighted_text)
    
    return highlighted_text

def format_message_content(content: str, sources: Optional[List[Dict[str, Any]]] = None) -> str:
    """Format message content with markdown and source highlighting."""
    # Apply source highlighting if available
    if sources:
        content = highlight_sources(content, sources)
    
    # Convert markdown to HTML (simple conversion for common elements)
    # Convert bold
    content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
    # Convert italic
    content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)
    # Convert code
    content = re.sub(r'`(.*?)`', r'<code>\1</code>', content)
    
    # Convert links
    content = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" target="_blank">\1</a>', content)
    
    # Convert newlines to <br>
    content = content.replace('\n', '<br>')
    
    return content

def display_source_info(sources: List[Dict[str, Any]]) -> None:
    """Display information about the sources used in the response."""
    if not sources:
        return
    
    st.markdown("##### Sources utilisées")
    
    for i, source in enumerate(sources):
        source_type = source.get("source_type", "inconnu")
        source_id = source.get("source_id", "inconnu")
        score = source.get("score", 0.0)
        
        # Format based on source type
        if source_type == "document":
            st.markdown(f"""
            <div style="padding: 10px; border-radius: 5px; background-color: #E3F2FD; margin-bottom: 5px;">
                <span style="font-weight: bold;">📄 Document #{source_id}</span> • 
                <span style="color: #666;">Score: {score:.2f}</span>
            </div>
            """, unsafe_allow_html=True)
        elif source_type == "note":
            st.markdown(f"""
            <div style="padding: 10px; border-radius: 5px; background-color: #FFF8E1; margin-bottom: 5px;">
                <span style="font-weight: bold;">📝 Note #{source_id}</span> • 
                <span style="color: #666;">Score: {score:.2f}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="padding: 10px; border-radius: 5px; background-color: #F5F5F5; margin-bottom: 5px;">
                <span style="font-weight: bold;">{source_type} #{source_id}</span> • 
                <span style="color: #666;">Score: {score:.2f}</span>
            </div>
            """, unsafe_allow_html=True)

def user_message(message: Dict[str, Any]) -> None:
    """Display a user message."""
    col1, col2 = st.columns([1, 12])
    
    with col1:
        st.markdown("""
        <div style="background-color: #1E88E5; color: white; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; font-weight: bold;">
            U
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        timestamp = format_time(message.get("created_at", ""))
        
        st.markdown(f"""
        <div style="background-color: #E3F2FD; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span style="font-weight: bold;">Vous</span>
                <span style="color: #666; font-size: 0.8rem;">{timestamp}</span>
            </div>
            <div>{message.get("content", "")}</div>
        </div>
        """, unsafe_allow_html=True)

def assistant_message(message: Dict[str, Any], sources: Optional[List[Dict[str, Any]]] = None) -> None:
    """Display an assistant message."""
    col1, col2 = st.columns([1, 12])
    
    with col1:
        st.markdown("""
        <div style="background-color: #43A047; color: white; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; font-weight: bold;">
            AI
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        timestamp = format_time(message.get("created_at", ""))
        content = format_message_content(message.get("content", ""), sources)
        
        st.markdown(f"""
        <div style="background-color: #F1F8E9; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span style="font-weight: bold;">Assistant</span>
                <span style="color: #666; font-size: 0.8rem;">{timestamp}</span>
            </div>
            <div>{content}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Display sources if available
        if sources:
            with st.expander("Afficher les sources", expanded=False):
                display_source_info(sources)

def system_message(content: str) -> None:
    """Display a system message."""
    st.markdown(f"""
    <div style="background-color: #F5F5F5; padding: 10px; border-radius: 5px; margin: 5px 0; text-align: center; font-style: italic; color: #666;">
        {content}
    </div>
    """, unsafe_allow_html=True)

def display_chat(
    messages: List[Dict[str, Any]],
    sources: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    on_send: Optional[Callable[[str], None]] = None,
    placeholder: str = "Tapez votre message...",
    key_prefix: str = ""
) -> None:
    """
    Display a chat interface with messages and an input box.
    
    Args:
        messages: List of message objects with role, content, etc.
        sources: Dictionary mapping message IDs to source information
        on_send: Callback function when user sends a message
        placeholder: Placeholder text for the input box
        key_prefix: Prefix for the session state keys
    """
    # Create a container for messages
    chat_container = st.container()
    
    # Display messages
    with chat_container:
        if not messages:
            system_message("Pas de messages dans cette conversation.")
        else:
            for message in messages:
                message_id = message.get("id")
                role = message.get("role")
                
                # Get sources for this message if available
                message_sources = sources.get(str(message_id)) if sources else None
                
                if role == "user":
                    user_message(message)
                elif role == "assistant":
                    assistant_message(message, message_sources)
                elif role == "system":
                    system_message(message.get("content", ""))
    
    # Input box for new messages
    input_key = f"{key_prefix}_message_input"
    
    # Use a form to prevent auto-refresh on input
    with st.form(key=f"{key_prefix}_message_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        
        with col1:
            user_input = st.text_area(
                "Message",
                placeholder=placeholder,
                key=input_key,
                height=80
            )
        
        with col2:
            st.write("")  # Add some space
            st.write("")  # Add some space
            submit_button = st.form_submit_button("📤 Envoyer")
        
        if submit_button and user_input and on_send:
            # Call the callback function with the user input
            on_send(user_input)

def display_typing_indicator() -> None:
    """Display a typing indicator to show that the assistant is generating a response."""
    typing_container = st.empty()
    
    for i in range(3):
        typing_container.markdown(f"""
        <div style="background-color: #F1F8E9; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
            <div style="font-weight: bold; margin-bottom: 5px;">Assistant</div>
            <div>{"⚫" * (i+1) + "⚪" * (3-i)}</div>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(0.3)
    
    # Clear the typing indicator
    typing_container.empty()

def display_sources_selector(
    sources: Dict[str, List[Dict[str, Any]]],
    active_sources: Dict[str, List[int]],
    on_toggle: Callable[[str, int, bool], None],
    key_prefix: str = ""
) -> None:
    """
    Display selectors for RAG sources and notes.
    
    Args:
        sources: Dictionary of available sources
        active_sources: Dictionary of active source IDs
        on_toggle: Callback when a source is toggled
        key_prefix: Prefix for the session state keys
    """
    with st.expander("Gérer les sources de connaissances", expanded=False):
        # RAG Corpus tab and Notes tab
        rag_tab, notes_tab = st.tabs(["📂 Corpus RAG", "🗒️ Notes"])
        
        # RAG Corpus tab
        with rag_tab:
            if not sources.get("rag_corpus"):
                st.info("Aucun corpus RAG disponible. Ajoutez-en un dans la section RAG Manager.")
            else:
                st.markdown("##### Corpus RAG disponibles")
                
                for corpus in sources.get("rag_corpus", []):
                    corpus_id = corpus.get("id")
                    corpus_name = corpus.get("name", f"Corpus #{corpus_id}")
                    is_active = corpus.get("is_active", False)
                    doc_count = corpus.get("document_count", 0)
                    
                    # Create a unique key for this checkbox
                    checkbox_key = f"{key_prefix}_rag_{corpus_id}"
                    
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        if st.checkbox(
                            f"{corpus_name} ({doc_count} documents)",
                            value=is_active,
                            key=checkbox_key,
                            help=f"Activer/désactiver le corpus '{corpus_name}'",
                        ):
                            # Add to active sources if not already there
                            if corpus_id not in active_sources.get("rag", []):
                                on_toggle("rag", corpus_id, True)
                        else:
                            # Remove from active sources if there
                            if corpus_id in active_sources.get("rag", []):
                                on_toggle("rag", corpus_id, False)
        
        # Notes tab
        with notes_tab:
            if not sources.get("notes"):
                st.info("Aucune note disponible. Ajoutez-en une dans la section Notes.")
            else:
                st.markdown("##### Notes disponibles")
                
                for note in sources.get("notes", []):
                    note_id = note.get("id")
                    note_title = note.get("title", f"Note #{note_id}")
                    is_active = note.get("is_active", False)
                    
                    # Create a unique key for this checkbox
                    checkbox_key = f"{key_prefix}_note_{note_id}"
                    
                    if st.checkbox(
                        note_title,
                        value=is_active,
                        key=checkbox_key,
                        help=f"Activer/désactiver la note '{note_title}'",
                    ):
                        # Add to active sources if not already there
                        if note_id not in active_sources.get("note", []):
                            on_toggle("note", note_id, True)
                    else:
                        # Remove from active sources if there
                        if note_id in active_sources.get("note", []):
                            on_toggle("note", note_id, False)