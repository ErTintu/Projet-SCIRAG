"""
SCIRAG Frontend Application
Main entry point for the Streamlit application.
"""

import streamlit as st
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="SCIRAG - Intelligent Conversational Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Main page
st.title("🧠 SCIRAG - Intelligent Conversational Assistant")
st.markdown("""
Welcome to SCIRAG, your intelligent conversational assistant with RAG capabilities.

### Features:
- 🔁 Persistent conversations
- 📂 PDF document integration
- 🗒️ Personal notes management  
- 🧠 Multiple LLM model support
- 🔍 Semantic search
""")

# Sidebar navigation
st.sidebar.title("Navigation")
st.sidebar.info("""
Use the sidebar to navigate between:
- Conversations
- RAG Manager
- LLM Configurations
- Notes
""")

# API connection check
api_url = os.getenv("API_URL", "http://localhost:8000")
try:
    import requests
    response = requests.get(f"{api_url}/health")
    if response.status_code == 200:
        st.sidebar.success("✅ API Connected")
    else:
        st.sidebar.error("❌ API Connection Failed")
except:
    st.sidebar.warning("⚠️ API Not Available")

# Footer
st.markdown("---")
st.markdown("© 2024 SCIRAG - Built with Streamlit and FastAPI")