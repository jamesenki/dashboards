"""
Tool Registry for the Agent Framework.
Handles registration, discovery and execution of tools that the agent can use.
"""

import json
import logging
import traceback
from typing import Any, Callable, Dict, List, Optional, Union

from src.ai.llm.llm_interface import LLMInterface
from src.ai.vector_db.vector_store import VectorStore
from src.config.ai_config import AgentConfig

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Tool Registry component of the Agent Framework.
    Responsible for registering, discovering, and executing tools.
    """

    def __init__(
        self,
        config: AgentConfig,
        vector_store: VectorStore,
        llm_interface: LLMInterface,
    ):
        """
        Initialize the Tool Registry with configuration and dependencies.

        Args:
            config: Agent configuration parameters
            vector_store: Vector database for tool discovery
            llm_interface: LLM interface for parameter extraction
        """
        self.config = config
        self.vector_store = vector_store
        self.llm_interface = llm_interface
        self.tools = {}  # Dictionary to store registered tools

    def register_tool(
        self, name: str, description: str, func: Callable, requires_params: bool = True
    ) -> None:
        """
        Register a tool with the registry.

        Args:
            name: Unique tool name
            description: Description of what the tool does and its parameters
            func: The function to call when the tool is executed
            requires_params: Whether the tool requires parameters
        """
        logger.debug(f"Registering tool: {name}")

        # Store the tool in the registry
        self.tools[name] = {
            "func": func,
            "description": description,
            "requires_params": requires_params,
        }

        # Add the tool description to the vector store for discovery
        document = f"{name}: {description}"
        metadata = {"tool_name": name, "requires_params": requires_params}

        self.vector_store.add_documents([document], [metadata])

    def get_relevant_tools(self, query: str, top_k: int = 5) -> List[str]:
        """
        Get tools relevant to the given query.

        Args:
            query: The user's query
            top_k: Maximum number of tools to return

        Returns:
            List of relevant tool names
        """
        logger.debug(f"Finding relevant tools for: {query[:50]}...")

        # Query the vector store for relevant tool descriptions
        results = self.vector_store.query_by_text(query, top_k=top_k)

        # Extract tool names from metadata
        tool_names = []
        for result in results:
            if "metadata" in result and "tool_name" in result["metadata"]:
                tool_names.append(result["metadata"]["tool_name"])

        return tool_names

    def execute_tool(self, tool_name: str, query: str) -> Any:
        """
        Execute a tool with the given query.

        Args:
            tool_name: Name of the tool to execute
            query: The user query for context

        Returns:
            The result of the tool execution
        """
        logger.debug(f"Executing tool {tool_name} for query: {query[:50]}...")

        # Check if the tool exists
        if tool_name not in self.tools:
            logger.error(f"Tool {tool_name} not found in registry")
            return f"Error: Tool '{tool_name}' not found"

        tool = self.tools[tool_name]

        try:
            # If the tool requires parameters, parse them from the query
            if tool["requires_params"]:
                params = self._parse_tool_params(query, tool["description"])
                return tool["func"](**params)
            else:
                # Execute the tool without parameters
                return tool["func"]()

        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}")
            logger.debug(traceback.format_exc())
            return f"Error executing tool {tool_name}: {str(e)}"

    def _parse_tool_params(self, query: str, tool_description: str) -> Dict[str, Any]:
        """
        Parse parameters for a tool from the user query.

        Args:
            query: The user's query
            tool_description: Description of the tool and its parameters

        Returns:
            Dictionary of parameter name/value pairs
        """
        logger.debug(f"Parsing parameters for query: {query[:50]}...")

        # Construct the prompt
        prompt = f"""
        Extract the parameters needed to execute a tool based on the following user query.
        Return the parameters as a valid JSON object.

        USER QUERY: {query}

        TOOL DESCRIPTION: {tool_description}

        Parameters should be extracted from the query and formatted as a JSON object.
        Example: {{"param1": "value1", "param2": 42}}

        PARAMETERS:
        """

        # Generate parameter JSON using the LLM
        json_str = self.llm_interface.generate(prompt, temperature=0.1, max_tokens=200)

        # Parse the JSON
        try:
            # Clean the JSON string (remove any non-JSON artifacts)
            json_str = self._clean_json_string(json_str)
            params = json.loads(json_str)
            return params
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing parameters JSON: {str(e)}")
            logger.debug(f"Raw JSON string: {json_str}")
            return {}  # Return empty dict on error

    def _clean_json_string(self, json_str: str) -> str:
        """
        Clean a JSON string to ensure it's valid.

        Args:
            json_str: The JSON string to clean

        Returns:
            A cleaned JSON string
        """
        # Find the first { and last } to extract just the JSON object
        start = json_str.find("{")
        end = json_str.rfind("}")

        if start != -1 and end != -1 and end > start:
            return json_str[start : end + 1]

        return json_str
