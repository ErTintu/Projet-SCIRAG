"""
LLM Model Selector Component for SCIRAG.
This module provides a UI component for selecting and configuring LLM models.
"""

import streamlit as st
from typing import Dict, List, Any, Optional, Callable
from services.api_client import get_api_client

def display_model_selector(
    llm_configs: List[Dict[str, Any]],
    active_config_id: Optional[int] = None,
    on_change: Optional[Callable[[int], None]] = None,
    key_prefix: str = "",
    show_test_button: bool = False
) -> int:
    """
    Display a selector for LLM configurations.
    
    Args:
        llm_configs: List of LLM configurations
        active_config_id: Currently active configuration ID
        on_change: Callback when configuration is changed
        key_prefix: Prefix for session state keys
        show_test_button: Whether to show a test button
        
    Returns:
        Selected configuration ID
    """
    # Sort configs by provider and name
    sorted_configs = sorted(
        llm_configs, 
        key=lambda x: (x.get("provider", ""), x.get("name", ""))
    )
    
    # Map configuration IDs to display names
    config_options = {}
    for config in sorted_configs:
        config_id = config.get("id")
        provider = config.get("provider", "").capitalize()
        name = config.get("name", "")
        model = config.get("model_name", "")
        
        display_name = f"{name} ({provider}: {model})"
        config_options[config_id] = display_name
    
    # If no configs available, show a message
    if not config_options:
        st.warning("Aucune configuration LLM disponible. Ajoutez-en une dans la section LLM Configs.")
        return None
    
    # Select the first config if none is active
    if active_config_id is None and sorted_configs:
        active_config_id = sorted_configs[0].get("id")
    
    # Create a unique key for this selector
    selector_key = f"{key_prefix}_llm_selector"
    
    # Display the selector
    col1, col2 = st.columns([3, 1]) if show_test_button else [st.columns([1])[0], None]
    
    with col1:
        selected_id = st.selectbox(
            "Modèle LLM",
            options=list(config_options.keys()),
            format_func=lambda x: config_options.get(x, f"Config #{x}"),
            index=list(config_options.keys()).index(active_config_id) if active_config_id in config_options else 0,
            key=selector_key
        )
    
    # Show test button if requested
    if show_test_button and col2:
        with col2:
            st.write("")  # Add some space
            if st.button("🧪 Tester", key=f"{key_prefix}_test_button"):
                with st.spinner("Test en cours..."):
                    # Get the selected configuration
                    selected_config = next(
                        (c for c in llm_configs if c.get("id") == selected_id),
                        None
                    )
                    
                    if selected_config:
                        try:
                            # Get API client
                            api_client = get_api_client()
                            
                            # Test the configuration
                            result = api_client.test_llm_config(selected_config)
                            
                            if result.get("success"):
                                st.success(f"✅ Test réussi: {result.get('message', '')}")
                            else:
                                st.error(f"❌ Échec du test: {result.get('message', 'Erreur inconnue')}")
                        except Exception as e:
                            st.error(f"❌ Échec du test: {str(e)}")
    
    # Call the callback if the selection has changed
    if on_change and selected_id != active_config_id:
        on_change(selected_id)
    
    return selected_id

def display_model_info(config: Dict[str, Any]) -> None:
    """
    Display information about a LLM configuration.
    
    Args:
        config: LLM configuration dictionary
    """
    if not config:
        st.info("Aucune configuration sélectionnée.")
        return
    
    # Extract config values
    provider = config.get("provider", "").capitalize()
    model = config.get("model_name", "")
    temperature = config.get("temperature", 0.7)
    max_tokens = config.get("max_tokens", 1024)
    
    # Display config info
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Provider", provider)
        st.metric("Modèle", model)
    
    with col2:
        st.metric("Température", f"{temperature:.1f}")
        st.metric("Tokens max", max_tokens)
    
    # Show additional info based on provider
    if provider.lower() == "local":
        api_url = config.get("api_url", "Non spécifié")
        st.info(f"**URL API locale:** `{api_url}`")
        st.markdown("""
        > **Note:** Le provider local nécessite [LM Studio](https://lmstudio.ai/) en cours d'exécution.
        """)