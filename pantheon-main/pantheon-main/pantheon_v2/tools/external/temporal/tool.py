import structlog
from zamp_public_workflow_sdk.temporal.temporal_service import (
    TemporalClientConfig,
    TemporalService,
)
from pantheon_v2.tools.external.temporal.config import TemporalConfig
from pantheon_v2.tools.external.temporal.models import (
    WorkflowParams,
    WorkflowResponse,
)
from pantheon_v2.tools.core.base import BaseTool
from pantheon_v2.tools.core.tool_registry import ToolRegistry
from zamp_public_workflow_sdk.temporal.models.temporal_models import RunWorkflowParams

logger = structlog.get_logger(__name__)


@ToolRegistry.register_tool(
    description="Temporal workflow tool for invoking and managing workflows",
)
class TemporalTool(BaseTool):
    def __init__(self, config: dict):
        self.client = None
        self.config = config

    async def initialize(self) -> None:
        pass

    @staticmethod
    async def get_api_handle(self):
        config = TemporalConfig(**self.config)

        temporal_client_config = TemporalClientConfig(
            host=config.host,
            namespace=config.namespace,
            is_cloud=config.is_cloud,
            client_cert=config.client_cert,
            client_key=config.client_key,
        )

        return await TemporalService.connect(temporal_client_config)

    @ToolRegistry.register_tool_action(description="Invoke a Temporal workflow")
    async def invoke_workflow(self, params: WorkflowParams) -> WorkflowResponse:
        """Invoke a Temporal workflow and return the result"""
        try:
            api = await TemporalTool.get_api_handle(self)

            result = await api.start_async_workflow(
                RunWorkflowParams(
                    workflow=params.workflow,
                    arg=params.arg,
                    task_queue=params.task_queue,
                    id=params.id,
                    retry_policy=params.retry_policy,
                )
            )

            return WorkflowResponse(
                workflow_id=params.id,
                run_id=result.run_id,
                result=result,
            )
        except Exception as e:
            logger.error("Workflow invocation failed", error=str(e))
            raise
