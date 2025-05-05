"""
Basic tests for database models using SQLite in-memory database for testing.
"""

import sys
import os
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the backend directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.connection import Base
from db.models import (
    LLMConfig,
    Conversation,
    Message,
    RAGCorpus,
    Document,
    DocumentChunk,
    Note,
    NoteChunk,
    ConversationContext
)

# Use SQLite in-memory database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test."""
    # Create SQLite in-memory engine for testing
    engine = create_engine(TEST_DATABASE_URL)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestSessionLocal()
    
    yield db
    
    # Clean up
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_create_llm_config(db):
    """Test creating an LLM configuration."""
    llm_config = LLMConfig(
        name="Test LLM",
        provider="openai",
        model_name="gpt-4",
        api_key="test-key",
        temperature=0.7,
        max_tokens=1024
    )
    db.add(llm_config)
    db.commit()
    
    assert llm_config.id is not None
    assert llm_config.name == "Test LLM"
    assert llm_config.provider == "openai"

def test_create_conversation_with_messages(db):
    """Test creating a conversation with messages."""
    # Create LLM config first
    llm_config = LLMConfig(
        name="Test LLM",
        provider="openai",
        model_name="gpt-4"
    )
    db.add(llm_config)
    db.commit()
    
    # Create conversation
    conversation = Conversation(
        title="Test Conversation",
        llm_config_id=llm_config.id
    )
    db.add(conversation)
    db.commit()
    
    # Add messages
    message1 = Message(
        conversation_id=conversation.id,
        role="user",
        content="Hello, how are you?"
    )
    message2 = Message(
        conversation_id=conversation.id,
        role="assistant",
        content="I'm doing well, thank you! How can I help you today?"
    )
    db.add(message1)
    db.add(message2)
    db.commit()
    
    # Reload conversation to get relationships
    db.refresh(conversation)
    
    # Verify
    assert len(conversation.messages) == 2
    assert conversation.messages[0].role == "user"
    assert conversation.messages[1].role == "assistant"

def test_create_rag_corpus_with_documents(db):
    """Test creating a RAG corpus with documents and chunks."""
    # Create RAG corpus
    corpus = RAGCorpus(
        name="Test Corpus",
        description="A test corpus for documents"
    )
    db.add(corpus)
    db.commit()
    
    # Add document
    document = Document(
        rag_corpus_id=corpus.id,
        filename="test.pdf",
        file_path="/path/to/test.pdf",
        file_type="pdf"
    )
    db.add(document)
    db.commit()
    
    # Add chunks
    chunk1 = DocumentChunk(
        document_id=document.id,
        chunk_text="This is the first chunk of text.",
        chunk_index=0
    )
    chunk2 = DocumentChunk(
        document_id=document.id,
        chunk_text="This is the second chunk of text.",
        chunk_index=1
    )
    db.add(chunk1)
    db.add(chunk2)
    db.commit()
    
    # Reload documents to get relationships
    db.refresh(corpus)
    db.refresh(document)
    
    # Verify
    assert len(corpus.documents) == 1
    assert len(document.chunks) == 2
    assert document.chunks[0].chunk_index == 0

def test_create_note_with_chunks(db):
    """Test creating a note with chunks."""
    # Create note
    note = Note(
        title="Test Note",
        content="This is a test note with some content that will be chunked."
    )
    db.add(note)
    db.commit()
    
    # Add chunks
    chunk1 = NoteChunk(
        note_id=note.id,
        chunk_text="This is a test note",
        chunk_index=0
    )
    chunk2 = NoteChunk(
        note_id=note.id,
        chunk_text="with some content that will be chunked.",
        chunk_index=1
    )
    db.add(chunk1)
    db.add(chunk2)
    db.commit()
    
    # Reload note to get relationships
    db.refresh(note)
    
    # Verify
    assert len(note.chunks) == 2
    assert note.chunks[1].chunk_index == 1

def test_conversation_context(db):
    """Test conversation context for RAG and notes."""
    # Create conversation
    conversation = Conversation(title="Test Conversation")
    db.add(conversation)
    
    # Create RAG corpus and note
    corpus = RAGCorpus(name="Test Corpus")
    note = Note(title="Test Note", content="Test content")
    db.add(corpus)
    db.add(note)
    db.commit()
    
    # Add context items
    rag_context = ConversationContext(
        conversation_id=conversation.id,
        context_type="rag",
        context_id=corpus.id,
        is_active=True
    )
    note_context = ConversationContext(
        conversation_id=conversation.id,
        context_type="note",
        context_id=note.id,
        is_active=False
    )
    db.add(rag_context)
    db.add(note_context)
    db.commit()
    
    # Reload conversation to get relationships
    db.refresh(conversation)
    
    # Verify
    assert len(conversation.context_items) == 2
    active_contexts = [ctx for ctx in conversation.context_items if ctx.is_active]
    assert len(active_contexts) == 1
    assert active_contexts[0].context_type == "rag"

def test_model_relationships(db):
    """Test model relationships and cascading deletes."""
    # Create a conversation with messages
    conversation = Conversation(title="Delete Test")
    db.add(conversation)
    db.commit()
    
    message = Message(
        conversation_id=conversation.id,
        role="user",
        content="Test message"
    )
    db.add(message)
    db.commit()
    
    # Verify message exists
    assert db.query(Message).count() == 1
    
    # Delete conversation (should cascade to messages)
    db.delete(conversation)
    db.commit()
    
    # Verify message was deleted
    assert db.query(Message).count() == 0

def test_model_to_dict_methods(db):
    """Test the to_dict methods on models."""
    # Create an LLM config
    llm_config = LLMConfig(
        name="Test LLM",
        provider="openai",
        model_name="gpt-4",
        temperature=0.7
    )
    db.add(llm_config)
    db.commit()
    
    # Test to_dict
    llm_dict = llm_config.to_dict()
    assert llm_dict["name"] == "Test LLM"
    assert llm_dict["provider"] == "openai"
    assert llm_dict["temperature"] == 0.7
    assert "created_at" in llm_dict
    
    # Create a conversation
    conversation = Conversation(
        title="Test Conversation",
        llm_config_id=llm_config.id
    )
    db.add(conversation)
    db.commit()
    
    # Test to_dict
    conv_dict = conversation.to_dict()
    assert conv_dict["title"] == "Test Conversation"
    assert conv_dict["llm_config_id"] == llm_config.id
    assert "created_at" in conv_dict

if __name__ == "__main__":
    pytest.main([__file__, "-v"])