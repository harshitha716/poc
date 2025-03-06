from pantheon_v2.tools.common.code_executor.tool import CodeExecutorTool
from pantheon_v2.tools.common.code_executor.config import CodeExecutorConfig
from pantheon_v2.tools.common.code_executor.models import (
    ExecuteCodeParams,
    ExecutionResult,
)

from pantheon_v2.tools.core.activity_registry import ActivityRegistry


@ActivityRegistry.register_activity(
    "Execute a Python function with resource constraints"
)
async def execute_code(
    config: CodeExecutorConfig, params: ExecuteCodeParams
) -> ExecutionResult:
    """Execute a Python function with the given arguments"""
    tool = CodeExecutorTool(config)
    await tool.initialize()
    try:
        return await tool.execute_code(params)
    finally:
        await tool.cleanup()
