"""
SCIRAG Frontend Application - Main entry point
"""

import streamlit as st
from services.api_client import get_api_client
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import time

# Configure page
st.set_page_config(
    page_title="SCIRAG - Assistant Conversationnel Intelligent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-title {
        font-size: 3rem !important;
        font-weight: 600 !important;
        margin-bottom: 1rem !important;
        color: #1E88E5;
    }
    .subtitle {
        font-size: 1.5rem !important;
        font-weight: 400 !important;
        margin-bottom: 2rem !important;
        color: #424242;
    }
    .card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
        margin-bottom: 1rem;
        border-left: 4px solid #1E88E5;
    }
    .card-title {
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #1E88E5;
    }
    .success-bg {
        background-color: #E8F5E9;
        border-left: 4px solid #4CAF50;
    }
    .warning-bg {
        background-color: #FFF8E1;
        border-left: 4px solid #FFC107;
    }
    .error-bg {
        background-color: #FFEBEE;
        border-left: 4px solid #F44336;
    }
    .footer {
        margin-top: 3rem;
        text-align: center;
        color: #9E9E9E;
    }
</style>
""", unsafe_allow_html=True)

# Get API client
api_client = get_api_client()

# Main header
st.markdown('<h1 class="main-title">🧠 SCIRAG</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Assistant Conversationnel Intelligent avec RAG</p>', unsafe_allow_html=True)

# Check API connection
api_status = api_client.check_health()
api_status_container = st.empty()

if api_status:
    api_status_container.markdown("""
    <div class="card success-bg">
        <div class="card-title">✅ API connectée</div>
        <p>Le backend est opérationnel et prêt à traiter vos requêtes.</p>
    </div>
    """, unsafe_allow_html=True)
else:
    api_status_container.markdown("""
    <div class="card error-bg">
        <div class="card-title">❌ API non disponible</div>
        <p>Impossible de se connecter au backend. Vérifiez que le serveur API est en cours d'exécution.</p>
    </div>
    """, unsafe_allow_html=True)

# Dashboard main content
col1, col2 = st.columns(2)

# First column - App overview
with col1:
    st.markdown("""
    <div class="card">
        <div class="card-title">📊 Vue d'ensemble</div>
        <p>SCIRAG est une application conversationnelle enrichie par RAG (Retrieval-Augmented Generation) qui permet d'intégrer des connaissances spécifiques dans vos conversations avec des modèles IA.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Features list
    st.markdown("### Principales fonctionnalités")
    st.markdown("""
    * 🔁 **Conversations persistantes** - Gardez un historique de toutes vos discussions
    * 📂 **Intégration de documents** - Enrichissez le contexte avec vos PDF
    * 🗒️ **Notes personnelles** - Créez et gérez des notes activables dans les conversations
    * 🧠 **LLM flexibles** - Utilisez Claude, GPT ou des modèles locaux
    * 🔍 **Recherche sémantique** - Trouvez rapidement l'information pertinente
    """)
    
    # Get started
    st.markdown("### Pour commencer")
    st.markdown("""
    1. Créez un corpus RAG avec vos documents dans la section **RAG Manager**
    2. Ajoutez des notes personnelles dans la section **Notes**
    3. Configurez votre modèle LLM préféré dans **LLM Configs**
    4. Commencez une nouvelle conversation dans **Conversations**
    """)

# Second column - Statistics (if API is connected)
with col2:
    if api_status:
        try:
            # Try to get conversations and RAG statistics
            conversations = api_client.get_conversations(limit=100)
            rag_stats = api_client.get_rag_statistics()
            
            # Display RAG statistics
            st.markdown("""
            <div class="card">
                <div class="card-title">📈 Statistiques</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Key metrics
            metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
            
            with metrics_col1:
                st.metric(label="Conversations", value=len(conversations))
            
            with metrics_col2:
                st.metric(label="Corpus RAG", value=rag_stats.get("rag_corpus_count", 0))
            
            with metrics_col3:
                st.metric(label="Notes", value=rag_stats.get("note_count", 0))
            
            # Embedding stats
            st.markdown("##### Système RAG")
            st.markdown(f"""
            - **Modèle d'embedding :** `{rag_stats.get('embedding_model', 'Non défini')}`
            - **Dimension des embeddings :** {rag_stats.get('embedding_dimension', 'N/A')}
            - **Stratégie de chunking :** {rag_stats.get('chunker_strategy', 'N/A')}
            - **Nombre de chunks :** {rag_stats.get('chunk_count', 0)}
            """)
            
            # If there are conversations, show a graph
            if conversations:
                # Count conversations per day
                conversation_dates = [
                    datetime.fromisoformat(c.get("created_at", "")).date() 
                    for c in conversations 
                    if "created_at" in c
                ]
                
                date_counts = {}
                for date in conversation_dates:
                    date_str = date.isoformat()
                    if date_str in date_counts:
                        date_counts[date_str] += 1
                    else:
                        date_counts[date_str] = 1
                
                # Create dataframe
                df = pd.DataFrame({
                    "Date": list(date_counts.keys()),
                    "Count": list(date_counts.values())
                })
                
                # Sort by date
                df["Date"] = pd.to_datetime(df["Date"])
                df = df.sort_values("Date")
                
                # Convert back to string for display
                df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
                
                # Create chart
                fig = px.bar(
                    df, 
                    x="Date", 
                    y="Count",
                    title="Conversations par jour", 
                    labels={"Count": "Nombre de conversations", "Date": "Date"}
                )
                
                # Customize chart
                fig.update_layout(
                    height=300,
                    margin=dict(l=10, r=10, t=40, b=10),
                )
                
                # Display chart
                st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.markdown(f"""
            <div class="card warning-bg">
                <div class="card-title">⚠️ Impossible de charger les statistiques</div>
                <p>Une erreur s'est produite lors de la récupération des statistiques.</p>
                <p><em>Détails: {str(e)}</em></p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="card warning-bg">
            <div class="card-title">⚠️ Statistiques non disponibles</div>
            <p>Connectez-vous à l'API pour voir les statistiques du système.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Show demo screenshot instead
        st.image("https://via.placeholder.com/600x300?text=Aperçu+des+statistiques", 
                 caption="Aperçu des statistiques (API non connectée)")

# Sidebar
st.sidebar.title("Navigation")
st.sidebar.info("""
Utilisez le menu pour naviguer entre les différentes sections :
- 🔁 **Conversations**
- 📂 **RAG Manager**
- ⚙️ **LLM Configs**
- 🗒️ **Notes**
""")

# API Connection status indicator in sidebar
if api_status:
    st.sidebar.success("✅ API Connectée")
else:
    st.sidebar.error("❌ API Non Disponible")
    st.sidebar.markdown("""
    Vérifiez que :
    1. Le serveur backend est démarré
    2. L'URL de l'API est correcte
    3. Le firewall n'est pas bloqué
    """)

# API URL and app info
api_url = os.getenv("API_URL", "http://localhost:8000")
st.sidebar.markdown(f"**URL API :** `{api_url}`")

# Auto refresh option
auto_refresh = st.sidebar.checkbox("Actualisation auto", value=False)
if auto_refresh:
    refresh_interval = st.sidebar.slider("Intervalle (secondes)", 5, 60, 30)
    st.sidebar.info(f"Actualisation toutes les {refresh_interval} secondes")
    
    # Add a placeholder for refresh status
    refresh_status = st.sidebar.empty()
    
    # Check if it's time to refresh
    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = time.time()
    
    # Check if refresh interval has passed
    current_time = time.time()
    if current_time - st.session_state.last_refresh > refresh_interval:
        # Update last refresh time
        st.session_state.last_refresh = current_time
        
        # Clear cache to force refresh
        api_client._clear_cache()
        
        # Show refresh status
        refresh_status.info("🔄 Actualisation en cours...")
        
        # This will force Streamlit to rerun the script
        st.experimental_rerun()

# Footer
st.markdown("""
<div class="footer">
    <p>© 2024 SCIRAG - Version 0.1.0</p>
    <p>Développé avec Streamlit & FastAPI</p>
</div>
""", unsafe_allow_html=True)