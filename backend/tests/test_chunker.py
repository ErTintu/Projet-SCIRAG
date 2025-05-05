# backend/tests/test_chunker.py
"""
Tests for the RAG chunker module.
"""

import os
import sys
import pytest
from typing import List, Dict, Any

# Add the parent directory to the path to import backend modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rag.chunker import (
    Chunk, Chunker, CharacterChunker, TokenChunker, 
    ParagraphChunker, SentenceChunker, ChunkerFactory
)


class TestChunk:
    """Tests for the Chunk class."""
    
    def test_chunk_creation(self):
        """Test creating a chunk."""
        chunk = Chunk(
            text="This is a test chunk",
            index=0,
            source_id=1,
            source_type="document"
        )
        
        assert chunk.text == "This is a test chunk"
        assert chunk.index == 0
        assert chunk.source_id == 1
        assert chunk.source_type == "document"
        assert chunk.metadata == {}
    
    def test_chunk_with_metadata(self):
        """Test creating a chunk with metadata."""
        metadata = {"author": "Test Author", "page": 1}
        chunk = Chunk(
            text="This is a test chunk",
            index=0,
            source_id=1,
            source_type="document",
            metadata=metadata
        )
        
        assert chunk.metadata == metadata
    
    def test_chunk_to_dict(self):
        """Test converting a chunk to a dictionary."""
        metadata = {"author": "Test Author", "page": 1}
        chunk = Chunk(
            text="This is a test chunk",
            index=0,
            source_id=1,
            source_type="document",
            metadata=metadata
        )
        
        chunk_dict = chunk.to_dict()
        assert chunk_dict["text"] == "This is a test chunk"
        assert chunk_dict["index"] == 0
        assert chunk_dict["source_id"] == 1
        assert chunk_dict["source_type"] == "document"
        assert chunk_dict["metadata"] == metadata
    
    def test_chunk_from_dict(self):
        """Test creating a chunk from a dictionary."""
        metadata = {"author": "Test Author", "page": 1}
        chunk_dict = {
            "text": "This is a test chunk",
            "index": 0,
            "source_id": 1,
            "source_type": "document",
            "metadata": metadata
        }
        
        chunk = Chunk.from_dict(chunk_dict)
        assert chunk.text == "This is a test chunk"
        assert chunk.index == 0
        assert chunk.source_id == 1
        assert chunk.source_type == "document"
        assert chunk.metadata == metadata
    
    def test_chunk_len(self):
        """Test getting the length of a chunk."""
        chunk = Chunk(
            text="This is a test chunk",
            index=0
        )
        
        assert len(chunk) == len("This is a test chunk")
    
    def test_chunk_str(self):
        """Test the string representation of a chunk."""
        chunk = Chunk(
            text="This is a test chunk",
            index=0,
            source_id=1,
            source_type="document"
        )
        
        assert str(chunk) == "Chunk(0, document:1, 20 chars)"


class TestCharacterChunker:
    """Tests for the CharacterChunker class."""
    
    def test_chunk_small_text(self):
        """Test chunking a small text."""
        chunker = CharacterChunker(chunk_size=100, chunk_overlap=20)
        text = "This is a small text."
        
        chunks = chunker.chunk_text(text, source_id=1, source_type="test")
        
        assert len(chunks) == 1
        assert chunks[0].text == text
        assert chunks[0].index == 0
        assert chunks[0].source_id == 1
        assert chunks[0].source_type == "test"

    @pytest.mark.slow
    def test_chunk_large_text(self):
        """Test chunking a large text."""
        chunker = CharacterChunker(chunk_size=20, chunk_overlap=5)
        text = "This is a text that will be split into chunks for testing."
        
        chunks = chunker.chunk_text(text, source_id=1, source_type="test")
        
        assert len(chunks) > 1
        # Check that the first chunk starts with the beginning of the text
        assert chunks[0].text.startswith("This is")
        # Check that each chunk has a different index
        indices = [chunk.index for chunk in chunks]
        assert len(indices) == len(set(indices))  # All indices should be unique
        # Check that the chunks cover the entire text
        full_text = " ".join(chunk.text for chunk in chunks)
        assert all(word in full_text for word in text.split())
    
    def test_chunk_with_newlines(self):
        """Test chunking text with newlines."""
        chunker = CharacterChunker(chunk_size=30, chunk_overlap=5)
        text = "This is a paragraph.\n\nThis is another paragraph.\n\nAnd a third one."
        
        chunks = chunker.chunk_text(text, source_id=1, source_type="test")
        
        assert len(chunks) > 1
        # Check that the chunker respects paragraph boundaries
        assert chunks[0].text == "This is a paragraph."
        assert chunks[1].text == "This is another paragraph."
        # Optionnel : vérifier le contenu du 3e chunk si nécessaire
        assert chunks[2].text == "And a third one."
        
    def test_empty_text(self):
        """Test chunking empty text."""
        chunker = CharacterChunker()
        text = ""
        
        chunks = chunker.chunk_text(text, source_id=1, source_type="test")
        
        assert len(chunks) == 0


class TestParagraphChunker:
    """Tests for the ParagraphChunker class."""
    
    def test_chunk_by_paragraphs(self):
        """Test chunking text by paragraphs."""
        chunker = ParagraphChunker()
        text = """This is the first paragraph.

This is the second paragraph.

This is the third paragraph.

This is the fourth paragraph."""
        
        chunks = chunker.chunk_text(text, source_id=1, source_type="test")
        
        # Should create one or two chunks depending on chunk_size
        assert len(chunks) >= 1
        assert "first paragraph" in chunks[0].text
        assert "second paragraph" in chunks[0].text
    
    def test_single_paragraph(self):
        """Test chunking a single paragraph."""
        chunker = ParagraphChunker()
        text = "This is a single paragraph without any newlines."
        
        chunks = chunker.chunk_text(text, source_id=1, source_type="test")
        
        assert len(chunks) == 1
        assert chunks[0].text == text
    
    def test_long_paragraphs(self):
        """Test chunking text with long paragraphs."""
        chunker = ParagraphChunker(chunk_size=50, max_paragraphs_per_chunk=1)
        text = """This is a very long paragraph that exceeds the chunk size limit.

This is another long paragraph that should be in a separate chunk."""
        
        chunks = chunker.chunk_text(text, source_id=1, source_type="test")
        
        assert len(chunks) == 3
        assert "very long paragraph" in chunks[0].text
        assert "another long paragraph" in chunks[1].text


class TestSentenceChunker:
    """Tests for the SentenceChunker class."""
    
    def test_chunk_by_sentences(self):
        """Test chunking text by sentences."""
        chunker = SentenceChunker(chunk_size=2, chunk_overlap=0)
        text = "This is the first sentence. This is the second sentence. This is the third sentence."
        
        chunks = chunker.chunk_text(text, source_id=1, source_type="test")
        
        assert len(chunks) == 2
        assert "first sentence" in chunks[0].text and "second sentence" in chunks[0].text
        assert "third sentence" in chunks[1].text
    
    def test_overlap(self):
        """Test sentence chunking with overlap."""
        chunker = SentenceChunker(chunk_size=2, chunk_overlap=1)
        text = "First. Second. Third. Fourth."
        
        chunks = chunker.chunk_text(text, source_id=1, source_type="test")
        
        assert len(chunks) == 3
        assert "First. Second." in chunks[0].text
        assert "Second. Third." in chunks[1].text
        assert "Third. Fourth." in chunks[2].text


class TestChunkerFactory:
    """Tests for the ChunkerFactory class."""
    
    def test_get_character_chunker(self):
        """Test getting a character chunker."""
        chunker = ChunkerFactory.get_chunker("character")
        assert isinstance(chunker, CharacterChunker)
    
    def test_get_paragraph_chunker(self):
        """Test getting a paragraph chunker."""
        chunker = ChunkerFactory.get_chunker("paragraph")
        assert isinstance(chunker, ParagraphChunker)
    
    def test_get_sentence_chunker(self):
        """Test getting a sentence chunker."""
        chunker = ChunkerFactory.get_chunker("sentence")
        assert isinstance(chunker, SentenceChunker)
    
    def test_get_token_chunker(self):
        """Test getting a token chunker."""
        chunker = ChunkerFactory.get_chunker("token")
        assert isinstance(chunker, TokenChunker)
    
    def test_invalid_strategy(self):
        """Test getting an invalid chunker strategy."""
        with pytest.raises(ValueError):
            ChunkerFactory.get_chunker("invalid_strategy")
    
    def test_custom_parameters(self):
        """Test passing custom parameters to a chunker."""
        chunker = ChunkerFactory.get_chunker("character", chunk_size=42, chunk_overlap=10)
        assert chunker.chunk_size == 42
        assert chunker.chunk_overlap == 10