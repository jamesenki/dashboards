"""
Cognitive Controller for the Agent Framework.
The main orchestration component that coordinates planning, memory, tools and LLM generation.
Implements the Multi-Modal Cognitive Protocol (MCP) architecture.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from src.ai.agent.memory_manager import MemoryManager
from src.ai.agent.planning_module import PlanningModule
from src.ai.agent.tool_registry import ToolRegistry
from src.ai.llm.llm_interface import LLMInterface
from src.config.ai_config import AgentConfig

logger = logging.getLogger(__name__)


class CognitiveController:
    """
    Cognitive Controller component of the Agent Framework.
    Implements the Multi-Modal Cognitive Protocol (MCP) architecture.
    Responsible for orchestrating the components to process user queries.
    """

    def __init__(
        self,
        config: AgentConfig,
        planning_module: PlanningModule,
        memory_manager: MemoryManager,
        tool_registry: ToolRegistry,
        llm_interface: LLMInterface,
    ):
        """
        Initialize the Cognitive Controller with all required components.

        Args:
            config: Agent configuration parameters
            planning_module: For planning and task decomposition
            memory_manager: For managing context and memories
            tool_registry: For accessing tools
            llm_interface: For generating text responses
        """
        self.config = config
        self.planning_module = planning_module
        self.memory_manager = memory_manager
        self.tool_registry = tool_registry
        self.llm_interface = llm_interface

    def process_query(self, query: str, refine_results: bool = False) -> str:
        """
        Process a user query through the cognitive workflow.

        Args:
            query: The user's query
            refine_results: Whether to iteratively refine the results

        Returns:
            The response to the user's query
        """
        logger.info(f"Processing query: {query[:50]}...")

        # 1. Retrieve relevant memories
        memories = self.memory_manager.get_relevant_memories(query)
        logger.debug(f"Retrieved {len(memories)} relevant memories")

        # 2. Create a plan
        plan = self.planning_module.create_plan(query, memories)
        logger.debug(f"Created plan with {len(plan)} steps")

        # 3. Determine if tools are needed
        use_tools = self.planning_module.should_use_tools(query)

        # 4. Execute tools if needed
        tool_results = []
        if use_tools:
            # Get required tools
            tools = self.planning_module.get_required_tools(
                query, self.tool_registry.get_relevant_tools(query)
            )
            logger.debug(f"Using tools: {tools}")

            # Execute each tool
            for tool_name in tools:
                result = self.tool_registry.execute_tool(tool_name, query)
                tool_results.append(f"Tool '{tool_name}' result: {result}")

        # 5. Generate response
        response = self._generate_response(query, memories, plan, tool_results)

        # 6. Refine if requested
        if refine_results:
            iterations = 0
            while (
                self.planning_module.needs_refinement(query, response)
                and iterations < self.config.max_iterations
            ):
                logger.debug(f"Refining response, iteration {iterations + 1}")
                response = self._refine_response(
                    query, memories, plan, tool_results, response
                )
                iterations += 1

        # 7. Store the interaction
        self.memory_manager.store_interaction(query, response)

        # 8. Reflect on the response if enabled
        if self.config.reflection_enabled:
            reflection = self.planning_module.reflect_on_response(query, response)
            self.memory_manager.store_reflection(reflection)

        return response

    def _generate_response(
        self, query: str, memories: List[str], plan: List[str], tool_results: List[str]
    ) -> str:
        """
        Generate a response based on the query, memories, plan, and tool results.

        Args:
            query: The user's query
            memories: Relevant memories
            plan: The execution plan
            tool_results: Results from any executed tools

        Returns:
            The generated response
        """
        # Construct the prompt
        prompt = f"""
        Generate a comprehensive response to the user's query using the provided information.

        USER QUERY: {query}

        RELEVANT CONTEXT:
        {self._format_list(memories)}

        EXECUTION PLAN:
        {self._format_list(plan)}

        TOOL RESULTS:
        {self._format_list(tool_results) if tool_results else "No tools were used."}

        Provide a clear, concise, and helpful response to the user's query.
        Base your response on the execution plan and tool results.
        Include relevant information from the context when appropriate.
        """

        # Generate the response
        return self.llm_interface.generate(prompt, temperature=0.7, max_tokens=500)

    def _refine_response(
        self,
        query: str,
        memories: List[str],
        plan: List[str],
        tool_results: List[str],
        previous_response: str,
    ) -> str:
        """
        Refine an existing response to improve its quality.

        Args:
            query: The user's query
            memories: Relevant memories
            plan: The execution plan
            tool_results: Results from any executed tools
            previous_response: The response to refine

        Returns:
            The refined response
        """
        # Construct the prompt
        prompt = f"""
        Review and improve the previous response to the user's query.

        USER QUERY: {query}

        PREVIOUS RESPONSE:
        {previous_response}

        RELEVANT CONTEXT:
        {self._format_list(memories)}

        EXECUTION PLAN:
        {self._format_list(plan)}

        TOOL RESULTS:
        {self._format_list(tool_results) if tool_results else "No tools were used."}

        Provide an improved response that addresses any deficiencies in the previous one.
        Be more thorough, clearer, more accurate, or more helpful as needed.
        """

        # Generate the refined response
        return self.llm_interface.generate(prompt, temperature=0.7, max_tokens=500)

    def _format_list(self, items: List[str]) -> str:
        """Format a list of items as a bulleted list."""
        if not items:
            return "None"

        return "\n".join([f"- {item}" for item in items])
