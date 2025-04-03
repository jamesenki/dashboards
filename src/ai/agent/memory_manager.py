"""
Memory Manager for the Agent Framework.
Handles storing and retrieving information about past interactions, user preferences, and agent reflections.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Union

from src.ai.vector_db.vector_store import VectorStore
from src.config.ai_config import AgentConfig

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Memory Manager component of the Agent Framework.
    Responsible for storing and retrieving agent memories using vector storage.
    """

    def __init__(self, config: AgentConfig, vector_store: VectorStore):
        """
        Initialize the Memory Manager with configuration and vector storage.

        Args:
            config: Agent configuration parameters
            vector_store: Vector database for storing and retrieving memories
        """
        self.config = config
        self.vector_store = vector_store
        self.max_memories = config.memory_size

    def store_interaction(self, query: str, response: str) -> str:
        """
        Store a user interaction (query and response) in memory.

        Args:
            query: The user's query
            response: The agent's response

        Returns:
            The ID of the stored memory
        """
        logger.debug(f"Storing interaction in memory: {query[:50]}...")

        # Combine query and response into a single document
        document = f"Query: {query}\nResponse: {response}"

        # Create metadata
        metadata = {
            "type": "interaction",
            "timestamp": time.time(),
            "query_length": len(query),
            "response_length": len(response),
        }

        # Store in vector database
        memory_ids = self.vector_store.add_documents([document], [metadata])

        return memory_ids[0] if memory_ids else ""

    def store_reflection(self, reflection: str) -> str:
        """
        Store an agent reflection in memory.

        Args:
            reflection: The agent's reflection on an interaction

        Returns:
            The ID of the stored memory
        """
        logger.debug(f"Storing reflection in memory: {reflection[:50]}...")

        # Create metadata
        metadata = {"type": "reflection", "timestamp": time.time()}

        # Store in vector database
        memory_ids = self.vector_store.add_documents([reflection], [metadata])

        return memory_ids[0] if memory_ids else ""

    def store_preference(self, preference: str) -> str:
        """
        Store a user preference in memory.

        Args:
            preference: The user's preference

        Returns:
            The ID of the stored memory
        """
        logger.debug(f"Storing user preference in memory: {preference[:50]}...")

        # Create metadata
        metadata = {"type": "preference", "timestamp": time.time()}

        # Store in vector database
        memory_ids = self.vector_store.add_documents([preference], [metadata])

        return memory_ids[0] if memory_ids else ""

    def get_relevant_memories(
        self, query: str, memory_types: Optional[List[str]] = None
    ) -> List[str]:
        """
        Retrieve memories relevant to the current query.

        Args:
            query: The current user query
            memory_types: Optional list of memory types to filter by (e.g., ["interaction", "preference"])

        Returns:
            List of relevant memory documents
        """
        logger.debug(f"Retrieving memories relevant to: {query[:50]}...")

        # If no memory types specified, use simple query with just query and top_k
        if not memory_types:
            # Query the vector database with positional arguments to match test expectations
            results = self.vector_store.query_by_text(query, top_k=self.max_memories)
        else:
            # For memory types filtering, use the filter_criteria argument
            filter_criteria = {"type": memory_types}
            results = self.vector_store.query_by_text(
                query, top_k=self.max_memories, filter_criteria=filter_criteria
            )

        # Extract and return the documents
        return [result["document"] for result in results]

    def clear_older_than(self, timestamp: float) -> None:
        """
        Clear memories older than the specified timestamp.

        Args:
            timestamp: Unix timestamp, memories older than this will be cleared
        """
        logger.debug(f"Clearing memories older than {timestamp}")

        # Query for memories older than the timestamp
        filter_criteria = {"timestamp": {"$lt": timestamp}}

        results = self.vector_store.query_by_text(
            query_text="",  # Empty query to match all documents
            filter_criteria=filter_criteria,
        )

        # Extract memory IDs
        memory_ids = [
            result["metadata"].get("id")
            for result in results
            if "id" in result["metadata"]
        ]

        # Delete memories if we have IDs and the vector store supports deletion
        if memory_ids and hasattr(self.vector_store, "delete_documents"):
            self.vector_store.delete_documents(memory_ids)
            logger.info(f"Cleared {len(memory_ids)} old memories")
