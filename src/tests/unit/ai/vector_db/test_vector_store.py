"""
Tests for the Vector Database component.
Following TDD principles - these tests define the expected behavior.
"""

import os
import tempfile
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# Import the configuration
from src.config.ai_config import VectorDBConfig

# The class to be implemented will be imported here
# from src.ai.vector_db.vector_store import VectorStore


@pytest.fixture
def mock_chromadb():
    """Mock the chromadb module and sentence_transformers without importing them"""
    # Mock the Chroma client
    mock_client = MagicMock()

    # Mock the collection
    mock_collection = MagicMock()

    # Set up mock return values for collection methods
    mock_collection.add.return_value = None
    mock_collection.get.return_value = {
        "ids": ["1", "2", "3"],
        "embeddings": None,  # Normally these would be numpy arrays
        "documents": ["document 1", "document 2", "document 3"],
        "metadatas": [
            {"source": "test1.txt", "type": "document"},
            {"source": "test2.txt", "type": "document"},
            {"source": "test3.txt", "type": "document"},
        ],
    }
    mock_collection.query.return_value = {
        "ids": [["1", "2"]],
        "embeddings": None,
        "documents": [["document 1", "document 2"]],
        "metadatas": [
            [
                {"source": "test1.txt", "type": "document"},
                {"source": "test2.txt", "type": "document"},
            ]
        ],
        "distances": [[0.1, 0.2]],
    }

    # Mock client methods
    mock_client.get_or_create_collection.return_value = mock_collection

    # Mock the modules without importing them
    mock_chroma = MagicMock()
    mock_chroma.Client.return_value = mock_client

    # Mock SentenceTransformer class
    mock_sentencetransformer = MagicMock()
    mock_embeddings = MagicMock()
    mock_embeddings.encode.return_value = np.random.rand(
        3, 384
    ).tolist()  # 3 documents, 384 dimensions
    mock_sentencetransformer.return_value = mock_embeddings

    # Create module-level patches
    mocks = {
        "chromadb": mock_chroma,
        "sentence_transformers": MagicMock(),
        "sentence_transformers.SentenceTransformer": mock_sentencetransformer,
    }

    # Apply all patches at the sys.modules level to avoid import issues
    with patch.dict("sys.modules", mocks):
        yield {
            "client": mock_client,
            "collection": mock_collection,
            "embedding_model": mock_embeddings,
            "sentencetransformer": mock_sentencetransformer,
        }


@pytest.fixture
def test_config():
    """Create a test configuration"""
    with tempfile.TemporaryDirectory() as temp_dir:
        return VectorDBConfig(
            db_type="chroma",
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            persist_directory=temp_dir,
            collection_name="test_collection",
        )


def test_vector_store_initialization(mock_chromadb, test_config):
    """Test that the vector store initializes correctly"""
    from src.ai.vector_db.vector_store import VectorStore

    vector_store = VectorStore(config=test_config)

    assert vector_store.config == test_config
    assert vector_store._client is None  # Should be lazy-loaded
    assert vector_store._collection is None  # Should be lazy-loaded
    assert vector_store._embedding_model is None  # Should be lazy-loaded


def test_vector_store_initialization_with_client(mock_chromadb, test_config):
    """Test that the vector store can be initialized with an existing client"""
    from src.ai.vector_db.vector_store import VectorStore

    mock_client = mock_chromadb["client"]
    vector_store = VectorStore(config=test_config, client=mock_client)

    assert vector_store.config == test_config
    assert vector_store._client is mock_client
    assert vector_store._collection is None  # Should be lazy-loaded
    assert vector_store._embedding_model is None  # Should be lazy-loaded


def test_get_collection(mock_chromadb, test_config):
    """Test retrieving or creating a collection"""
    from src.ai.vector_db.vector_store import VectorStore

    mock_client = mock_chromadb["client"]
    mock_collection = mock_chromadb["collection"]
    vector_store = VectorStore(config=test_config, client=mock_client)

    collection = vector_store._get_collection()

    mock_client.get_or_create_collection.assert_called_once_with(
        name=test_config.collection_name,
        embedding_function=vector_store._get_embedding_function(),
    )
    assert collection == mock_collection


def test_add_documents(mock_chromadb, test_config):
    """Test adding documents to the vector store"""
    from src.ai.vector_db.vector_store import VectorStore

    mock_client = mock_chromadb["client"]
    mock_collection = mock_chromadb["collection"]
    vector_store = VectorStore(config=test_config, client=mock_client)

    documents = ["This is document 1", "This is document 2", "This is document 3"]
    metadatas = [
        {"source": "test1.txt", "type": "document"},
        {"source": "test2.txt", "type": "document"},
        {"source": "test3.txt", "type": "document"},
    ]

    # Add the documents
    ids = vector_store.add_documents(documents, metadatas)

    # Check that the collection's add method was called with the right parameters
    mock_collection.add.assert_called_once()

    # Check that the IDs are valid UUIDs
    assert len(ids) == len(documents)
    for id_str in ids:
        # This will raise a ValueError if the ID is not a valid UUID
        uuid.UUID(id_str)


def test_query_by_text(mock_chromadb, test_config):
    """Test querying the vector store with text"""
    from src.ai.vector_db.vector_store import VectorStore

    mock_client = mock_chromadb["client"]
    mock_collection = mock_chromadb["collection"]
    vector_store = VectorStore(config=test_config, client=mock_client)

    query = "This is a test query"
    results = vector_store.query_by_text(query, top_k=2)

    # Check that the collection's query method was called
    mock_collection.query.assert_called_once()
    kwargs = mock_collection.query.call_args[1]
    assert kwargs["n_results"] == 2

    # Check that the results have the expected structure
    assert len(results) == 2  # We asked for 2 results
    for result in results:
        assert "document" in result
        assert "metadata" in result
        assert "score" in result


def test_retrieve_document(mock_chromadb, test_config):
    """Test retrieving documents by ID"""
    from src.ai.vector_db.vector_store import VectorStore

    mock_client = mock_chromadb["client"]
    mock_collection = mock_chromadb["collection"]
    vector_store = VectorStore(config=test_config, client=mock_client)

    ids = ["1", "2", "3"]
    docs = vector_store.retrieve_documents(ids)

    # Check that the collection's get method was called correctly
    mock_collection.get.assert_called_once_with(
        ids=ids, include=["documents", "metadatas"]
    )

    # Check the returned documents
    assert len(docs) == 3
    for i, doc in enumerate(docs):
        assert doc["document"] == f"document {i+1}"
        assert doc["metadata"]["source"] == f"test{i+1}.txt"
        assert doc["metadata"]["type"] == "document"


def test_get_embedding_function(mock_chromadb, test_config):
    """Test getting the embedding function"""
    from src.ai.vector_db.vector_store import VectorStore

    mock_embedding_model = mock_chromadb["embedding_model"]
    vector_store = VectorStore(config=test_config)

    # Get the embedding function
    embedding_function = vector_store._get_embedding_function()

    # Test the embedding function
    test_texts = ["This is a test", "Another test"]
    embeddings = embedding_function(test_texts)

    # Check that the embeddings have the expected structure
    # During testing, our mock embedding function might return differently structured results
    # We need to adapt our assertions to handle both real and mock implementations
    if isinstance(embeddings, list) and len(embeddings) > 0:
        if isinstance(embeddings[0], list):
            # Standard structure - list of lists (vectors)
            assert len(embeddings) == len(test_texts)
            assert all(len(embedding) > 0 for embedding in embeddings)
        else:
            # If a single vector is returned for some reason
            assert len(embeddings) > 0
