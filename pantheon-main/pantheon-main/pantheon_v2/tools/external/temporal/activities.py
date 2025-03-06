from pantheon_v2.tools.external.temporal.tool import TemporalTool
from pantheon_v2.tools.external.temporal.config import TemporalConfig
from pantheon_v2.tools.external.temporal.models import (
    WorkflowParams,
    WorkflowResponse,
)

from pantheon_v2.tools.core.activity_registry import ActivityRegistry


@ActivityRegistry.register_activity("Invoke a Temporal workflow")
async def invoke_workflow(
    config: TemporalConfig, params: WorkflowParams
) -> WorkflowResponse:
    tool = TemporalTool(config)
    await tool.initialize()
    return await tool.invoke_workflow(params)
