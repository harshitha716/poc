import asyncio
from typing import Optional

from zamp_public_workflow_sdk.temporal.temporal_service import (
    TemporalClientConfig,
    TemporalService,
)
from zamp_public_workflow_sdk.temporal.temporal_worker import TemporalWorkerConfig
from zamp_public_workflow_sdk.temporal.codec.large_payload_codec import (
    LargePayloadCodec,
)
from zamp_public_workflow_sdk.temporal.data_converters.base import BaseDataConverter
from zamp_public_workflow_sdk.temporal.data_converters.pydantic_payload_converter import (
    PydanticPayloadConverter,
)

from pantheon_v2.core.temporal.activities.registry import get_registered_activities
from pantheon_v2.core.temporal.workflows.registry import get_registered_workflows

from pantheon_v2.settings.settings import Settings, LOCAL
from pantheon_v2.core.temporal.constants import TASK_QUEUE

import structlog

from zamp_public_workflow_sdk.temporal.interceptors.tracing_interceptor import (
    TraceInterceptor,
)
from pantheon_v2.utils.trace_utils import TRACE_ID_CONTEXT_KEY, TRACE_ID_HEADER_KEY

logger = structlog.get_logger(__name__)


class TemporalWorkerManager:
    def __init__(self):
        client_cert, client_key = Settings.get_temporal_certs()
        self.client_config = TemporalClientConfig(
            host=Settings.TEMPORAL_HOST,
            namespace=Settings.TEMPORAL_NAMESPACE,
            is_cloud=Settings.is_cloud(),
            client_cert=client_cert,
            client_key=client_key,
            data_converter=BaseDataConverter()
            .replace_payload_codec(
                LargePayloadCodec(
                    Settings.GCP_PROJECT_ID, Settings.TEMPORAL_LARGE_PAYLOAD_BUCKET
                )
            )
            .replace_payload_converter(PydanticPayloadConverter),
        )

        self.task_queue = TASK_QUEUE
        self._service: Optional[TemporalService] = None

    async def start(self):
        """Initialize and start the Temporal worker."""
        try:
            logger.info(
                "Attempting to connect to Temporal server",
                host=self.client_config.host,
                namespace=self.client_config.namespace,
            )

            self._service = await TemporalService.connect(self.client_config)
            logger.info("Successfully connected to Temporal service")

            worker_config = TemporalWorkerConfig(
                task_queue=self.task_queue,
                activities=get_registered_activities(),
                workflows=get_registered_workflows(),
                interceptors=[
                    TraceInterceptor(
                        trace_header_key=TRACE_ID_HEADER_KEY,
                        trace_context_key=TRACE_ID_CONTEXT_KEY,
                        logger_module=structlog,
                        context_bind_fn=structlog.contextvars.bind_contextvars,
                    )
                ],
                disable_sandbox=Settings.ENVIRONMENT == LOCAL,
                debug_mode=Settings.ENVIRONMENT == LOCAL,
            )

            worker = await self._service.worker(worker_config)
            logger.info("Starting Temporal worker", task_queue=self.task_queue)
            await worker.run()

        except Exception as e:
            logger.error(
                "Failed to start Temporal worker",
                error=str(e),
                host=self.client_config.host,
                namespace=self.client_config.namespace,
            )
            raise


async def run_worker():
    """Helper function to run a worker with the specified configuration."""
    worker_manager = TemporalWorkerManager()
    await worker_manager.start()


if __name__ == "__main__":
    asyncio.run(run_worker())
