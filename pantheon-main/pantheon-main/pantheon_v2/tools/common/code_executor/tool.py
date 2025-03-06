import structlog
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

from pantheon_v2.tools.core.base import BaseTool
from pantheon_v2.tools.core.tool_registry import ToolRegistry
from pantheon_v2.tools.common.code_executor.config import CodeExecutorConfig
from pantheon_v2.tools.common.code_executor.models import (
    ExecuteCodeParams,
    ExecutionResult,
)
from pantheon_v2.utils.type_utils import import_module_safely

logger = structlog.get_logger(__name__)


@ToolRegistry.register_tool(
    description="Tool for executing Python functions with timeout constraints"
)
class CodeExecutorTool(BaseTool):
    def __init__(self, config: CodeExecutorConfig):
        self.config = config if config else CodeExecutorConfig()
        self.thread_pool = ThreadPoolExecutor()

    async def initialize(self) -> None:
        """Initialize the code executor tool"""
        logger.info("Code executor tool initialized successfully")

    @ToolRegistry.register_tool_action(
        description="Execute a Python function with given arguments"
    )
    async def execute_code(self, params: ExecuteCodeParams) -> ExecutionResult:
        """Execute the provided function with given arguments"""
        start_time = time.time()
        try:
            if isinstance(params.function, str):
                try:
                    module_name, function_name = params.function.rsplit(".", 1)
                except ValueError:
                    raise ValueError(
                        f"Invalid function path format: {params.function}. Expected format: 'module.path.function'"
                    )

                module = import_module_safely(module_name)
                params.function = getattr(module, function_name)

            if not callable(params.function):
                raise ValueError("Provided function is not callable")

            if asyncio.iscoroutinefunction(params.function):
                result = await params.function(*params.args, **params.kwargs)
            else:
                # Execute the function in a thread pool with timeout
                loop = asyncio.get_event_loop()

                def func_wrapper():
                    return self._execute_function(
                        params.function, *params.args, **params.kwargs
                    )

                result = await asyncio.wait_for(
                    loop.run_in_executor(self.thread_pool, func_wrapper),
                    timeout=self.config.timeout_seconds,
                )

            execution_time = time.time() - start_time

            return ExecutionResult(
                success=True, result=result, execution_time=execution_time
            )

        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            logger.error("Function execution timed out")
            return ExecutionResult(
                success=False,
                error=f"Execution timed out after {self.config.timeout_seconds} seconds",
                execution_time=execution_time,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                "Failed to execute function",
                error=str(e),
                function=params.function.__name__
                if hasattr(params.function, "__name__")
                else "unknown",
            )
            return ExecutionResult(
                success=False, error=str(e), execution_time=execution_time
            )

    def _execute_function(self, func: Callable, *args, **kwargs) -> Any:
        """Execute the function with given arguments"""
        return func(*args, **kwargs)

    async def cleanup(self) -> None:
        """Cleanup resources"""
        self.thread_pool.shutdown(wait=True)
