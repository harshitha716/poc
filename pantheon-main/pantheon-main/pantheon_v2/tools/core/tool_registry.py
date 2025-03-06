from functools import wraps
from typing import Dict, Callable, Any
from pantheon_v2.tools.core.models import Tool


class ToolRegistry:
    _tools: Dict[str, Tool] = {}

    @classmethod
    def register_tool(cls, description: str):
        """
        Register a tool decorator with optional description
        """

        def decorator(tool_class):
            tool_name = tool_class.__name__
            if tool_name not in cls._tools:
                cls._tools[tool_name] = Tool(tool_name, "")

            cls._tools[tool_name].description = description
            return tool_class

        return decorator

    @classmethod
    def register_tool_action(cls, description: str) -> Callable:
        """
        Register a tool action decorator with description
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await func(*args, **kwargs)

            # Get the class name from the function's qualified name
            tool_name = func.__qualname__.split(".")[0]

            # If the tool doesn't exist yet, create it (this can happen due to decoration order)
            if tool_name not in cls._tools:
                cls._tools[tool_name] = Tool(tool_name, "")

            cls._tools[tool_name].add_action(func.__name__, async_wrapper, description)
            return async_wrapper

        return decorator

    @classmethod
    async def execute_tool_action(
        cls,
        tool_name: str,
        action_name: str,
        **action_params: Any,
    ) -> Any:
        """Execute a tool action using provided tool instances.

        Args:
            tool_name: Name of the tool to use
            action_name: Name of the action to execute
            **action_params: Parameters to pass to the action

        Returns:
            Result of the action execution

        Raises:
            ValueError: If tool not found in provided instances
        """
        if tool_name not in cls._tools:
            raise ValueError(
                f"Tool '{tool_name}' not found in provided tool instances. Available tools: {cls._tools.keys()}"
            )

        tool_actions = cls._tools[tool_name]

        tool_action = tool_actions.get_action(action_name)
        if tool_action is None:
            raise ValueError(
                f"Action '{action_name}' not found in tool '{tool_name}'. Available actions: {tool_actions}"
            )

        return await tool_action(**action_params)

    # TODO (Giri): Add methods to get the tool actions that helps the LLM understand the tool
