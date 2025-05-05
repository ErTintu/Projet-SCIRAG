"""
Script to test the API routes using the requests library.

This script:
1. Creates a new LLM config
2. Creates a new conversation
3. Creates a new note
4. Sends a message
5. Prints the results

Run this after the API is running with:
python scripts/test_api.py
"""

import requests
import json
import sys
import os
from pprint import pprint

# Add the backend directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# API Base URL
API_URL = "http://localhost:8000/api"

def print_section(title):
    """Print a section title."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)

def test_llm_configs():
    """Test LLM config endpoints."""
    print_section("Testing LLM Config Endpoints")
    
    # Create LLM config
    print("\n>> Creating new LLM config...")
    llm_config = {
        "name": "Test OpenAI",
        "provider": "openai",
        "model_name": "gpt-4",
        "api_key": "test-key",
        "temperature": 0.7,
        "max_tokens": 1024
    }
    
    response = requests.post(f"{API_URL}/llm/configs", json=llm_config)
    if response.status_code == 201:
        llm_config_id = response.json()["id"]
        print(f"Created LLM config with ID: {llm_config_id}")
    else:
        print(f"Failed to create LLM config: {response.status_code}")
        print(response.json())
        llm_config_id = None
    
    # List LLM configs
    print("\n>> Listing LLM configs...")
    response = requests.get(f"{API_URL}/llm/configs")
    if response.status_code == 200:
        configs = response.json()
        print(f"Found {len(configs)} LLM configs:")
        for config in configs:
            print(f"  - {config['name']} ({config['provider']}/{config['model_name']})")
    else:
        print(f"Failed to list LLM configs: {response.status_code}")
        print(response.json())
    
    return llm_config_id

def test_conversations(llm_config_id=None):
    """Test conversation endpoints."""
    print_section("Testing Conversation Endpoints")
    
    # Create conversation
    print("\n>> Creating new conversation...")
    conversation = {
        "title": "Test Conversation",
    }
    if llm_config_id:
        conversation["llm_config_id"] = llm_config_id
    
    response = requests.post(f"{API_URL}/conversations", json=conversation)
    if response.status_code == 201:
        conversation_id = response.json()["id"]
        print(f"Created conversation with ID: {conversation_id}")
    else:
        print(f"Failed to create conversation: {response.status_code}")
        print(response.json())
        conversation_id = None
    
    # List conversations
    print("\n>> Listing conversations...")
    response = requests.get(f"{API_URL}/conversations")
    if response.status_code == 200:
        conversations = response.json()
        print(f"Found {len(conversations)} conversations:")
        for conv in conversations:
            print(f"  - {conv['title']} (ID: {conv['id']})")
    else:
        print(f"Failed to list conversations: {response.status_code}")
        print(response.json())
    
    return conversation_id

def test_notes():
    """Test note endpoints."""
    print_section("Testing Note Endpoints")
    
    # Create note
    print("\n>> Creating new note...")
    note = {
        "title": "Test Note",
        "content": "This is a test note with some important information. It should be chunked and embedded."
    }
    
    response = requests.post(f"{API_URL}/notes", json=note)
    if response.status_code == 201:
        note_id = response.json()["id"]
        print(f"Created note with ID: {note_id}")
    else:
        print(f"Failed to create note: {response.status_code}")
        print(response.json())
        note_id = None
    
    # List notes
    print("\n>> Listing notes...")
    response = requests.get(f"{API_URL}/notes")
    if response.status_code == 200:
        notes = response.json()
        print(f"Found {len(notes)} notes:")
        for note in notes:
            print(f"  - {note['title']} (ID: {note['id']})")
    else:
        print(f"Failed to list notes: {response.status_code}")
        print(response.json())
    
    return note_id

def test_send_message(conversation_id, note_id=None):
    """Test send message endpoint."""
    print_section("Testing Send Message Endpoint")
    
    if not conversation_id:
        print("Cannot send message: No conversation ID")
        return
    
    # Send message
    print("\n>> Sending message...")
    message = {
        "content": "Hello, this is a test message!"
    }
    
    if note_id:
        message["active_notes"] = [note_id]
    
    response = requests.post(f"{API_URL}/conversations/{conversation_id}/send", json=message)
    if response.status_code == 200:
        result = response.json()
        print("\nMessage sent successfully!")
        print("\nUser message:")
        print(f"  {result['user_message']['content']}")
        print("\nAssistant response:")
        print(f"  {result['assistant_message']['content']}")
    else:
        print(f"Failed to send message: {response.status_code}")
        print(response.json())

def test_rag_corpus():
    """Test RAG corpus endpoints."""
    print_section("Testing RAG Corpus Endpoints")
    
    # Create RAG corpus
    print("\n>> Creating new RAG corpus...")
    corpus = {
        "name": "Test Corpus",
        "description": "A test corpus for documents"
    }
    
    response = requests.post(f"{API_URL}/rag/corpus", json=corpus)
    if response.status_code == 201:
        corpus_id = response.json()["id"]
        print(f"Created RAG corpus with ID: {corpus_id}")
    else:
        print(f"Failed to create RAG corpus: {response.status_code}")
        print(response.json())
        corpus_id = None
    
    # List RAG corpus
    print("\n>> Listing RAG corpus...")
    response = requests.get(f"{API_URL}/rag/corpus")
    if response.status_code == 200:
        corpora = response.json()
        print(f"Found {len(corpora)} RAG corpora:")
        for corpus in corpora:
            print(f"  - {corpus['name']} (ID: {corpus['id']})")
    else:
        print(f"Failed to list RAG corpus: {response.status_code}")
        print(response.json())
    
    return corpus_id

def main():
    """Main function."""
    print("Testing SCIRAG API...")
    
    # Test all endpoints
    llm_config_id = test_llm_configs()
    conversation_id = test_conversations(llm_config_id)
    note_id = test_notes()
    corpus_id = test_rag_corpus()
    test_send_message(conversation_id, note_id)
    
    print("\n" + "=" * 80)
    print(" API Test Complete ".center(80, "="))
    print("=" * 80)
    print(f"\nIDs: LLM Config: {llm_config_id}, Conversation: {conversation_id}, Note: {note_id}, RAG Corpus: {corpus_id}")

if __name__ == "__main__":
    main()