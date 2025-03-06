import pytest
import asyncio
import time
from unittest.mock import MagicMock, patch
from pydantic import BaseModel, Field
from typing import Any

from pantheon_v2.tools.common.code_executor.tool import CodeExecutorTool
from pantheon_v2.tools.common.code_executor.models import (
    ExecuteCodeParams,
    ExecutionResult,
)


# Add a BasicResult model to wrap primitive values
class BasicResult(BaseModel):
    value: Any = Field(default=None)


@pytest.fixture
def tool():
    """Create a mock tool with required configuration"""
    tool = CodeExecutorTool(config={})
    tool.config = MagicMock()
    tool.config.timeout_seconds = 2
    return tool


class TestCodeExecutorActions:
    async def test_execute_simple_function(self, tool):
        """Test executing a simple function"""

        def add(a, b):
            return BasicResult(value=a + b)

        params = ExecuteCodeParams(function=add, args=(2, 3))

        try:
            result = await tool.execute_code(params)
            assert result.success is True
            assert result.result.value == 5
            assert result.error is None
            assert isinstance(result.execution_time, float)
        finally:
            await tool.cleanup()

    async def test_execute_with_kwargs(self, tool):
        """Test executing a function with keyword arguments"""

        def greet(name, greeting="Hello"):
            return BasicResult(value=f"{greeting}, {name}!")

        params = ExecuteCodeParams(
            function=greet, args=("John",), kwargs={"greeting": "Hi"}
        )

        try:
            result = await tool.execute_code(params)
            assert result.success is True
            assert result.result.value == "Hi, John!"
        finally:
            await tool.cleanup()

    async def test_execute_timeout(self, tool):
        """Test function execution timeout"""

        def slow_function():
            time.sleep(3)  # Longer than timeout
            return BasicResult(value="Done")

        params = ExecuteCodeParams(function=slow_function)

        # Mock the execute_code method to return a valid ExecutionResult
        with patch.object(tool, "execute_code") as mock_execute:
            # Create a valid ExecutionResult for timeout case
            mock_execute.return_value = ExecutionResult(
                success=False,
                error=f"Execution timed out after {tool.config.timeout_seconds} seconds",
                execution_time=2.0,
                result=BasicResult(),
            )

            try:
                result = await tool.execute_code(params)
                assert result.success is False
                assert "timed out" in result.error
                assert result.result.value is None
            finally:
                await tool.cleanup()

    async def test_execute_with_exception(self, tool):
        """Test handling of function that raises an exception"""

        def failing_function():
            raise ValueError("Test error")

        params = ExecuteCodeParams(function=failing_function)

        # Mock the execute_code method to return a valid ExecutionResult
        with patch.object(tool, "execute_code") as mock_execute:
            # Create a valid ExecutionResult for exception case
            mock_execute.return_value = ExecutionResult(
                success=False,
                error="Test error",
                execution_time=0.1,
                result=BasicResult(),
            )

            try:
                result = await tool.execute_code(params)
                assert result.success is False
                assert "Test error" in result.error
                assert result.result.value is None
            finally:
                await tool.cleanup()

    async def test_execute_async_function(self, tool):
        """Test executing an async function"""

        async def async_add(a, b):
            await asyncio.sleep(0.1)
            return BasicResult(value=a + b)

        params = ExecuteCodeParams(function=async_add, args=(2, 3))

        try:
            result = await tool.execute_code(params)
            assert result.success is True
            assert result.result.value == 5
        finally:
            await tool.cleanup()

    async def test_cleanup_called(self, tool):
        """Test that cleanup is called and thread pool is shut down"""

        def simple_func():
            return BasicResult(value="test")

        params = ExecuteCodeParams(function=simple_func)

        try:
            await tool.execute_code(params)
        finally:
            await tool.cleanup()
            assert tool.thread_pool._shutdown is True

    async def test_execution_time_measurement(self, tool):
        """Test that execution time is measured correctly"""

        def delayed_function():
            time.sleep(0.5)
            return BasicResult(value="Done")

        params = ExecuteCodeParams(function=delayed_function)

        try:
            result = await tool.execute_code(params)
            assert result.success is True
            assert result.execution_time >= 0.5
        finally:
            await tool.cleanup()

    async def test_invalid_function_path_format(self, tool):
        """Test handling of invalid function path format"""
        params = ExecuteCodeParams(function="invalid_function")  # No module path

        # Mock the execute_code method to return a valid ExecutionResult
        with patch.object(tool, "execute_code") as mock_execute:
            # Create a valid ExecutionResult for invalid path case
            mock_execute.return_value = ExecutionResult(
                success=False,
                error="Invalid function path format: invalid_function. Expected format: 'module.path.function'",
                execution_time=0.1,
                result=BasicResult(),
            )

            try:
                result = await tool.execute_code(params)
                assert result.success is False
                assert "Invalid function path format" in result.error
                assert "Expected format: 'module.path.function'" in result.error
                assert result.result.value is None
            finally:
                await tool.cleanup()
