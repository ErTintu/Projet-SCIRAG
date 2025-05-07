import streamlit as st
from services.api_client import APIClient

# Create API client
api_client = APIClient()

# Test health check
health_status = api_client.check_health()
st.write(f"API Health Status: {'✅ Connected' if health_status else '❌ Not Connected'}")

# If connected, try to get conversations
if health_status:
    try:
        conversations = api_client.get_conversations()
        st.write(f"Successfully retrieved {len(conversations)} conversations")
        
        # Display first conversation if available
        if conversations:
            st.write("First conversation:", conversations[0])
    except Exception as e:
        st.error(f"Error getting conversations: {str(e)}")