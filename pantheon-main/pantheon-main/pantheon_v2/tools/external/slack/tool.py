import structlog

from pantheon_v2.tools.core.base import BaseTool
from pantheon_v2.tools.core.tool_registry import ToolRegistry
from pantheon_v2.tools.external.slack.config import SlackConfig
from pantheon_v2.tools.external.slack.models import (
    SlackMessageRequest,
    SlackMessageResponse,
)
from pantheon_v2.utils.api_client import ApiClient, HttpMethod
from pantheon_v2.tools.external.slack.constants import (
    DEFAULT_HEADERS,
    API_ENDPOINT,
)

logger = structlog.get_logger(__name__)


@ToolRegistry.register_tool(
    description="Slack API tool for sending messages",
)
class SlackTool(BaseTool):
    def __init__(self, config: SlackConfig):
        self.config: SlackConfig = config
        self.client: ApiClient = ApiClient(
            base_url=self.config.api_base_url,
            default_headers=DEFAULT_HEADERS,
        )

    async def initialize(self) -> None:
        """Initialize the Slack API client"""
        try:
            logger.info("Slack tool initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Slack tool", error=str(e))
            raise

    @ToolRegistry.register_tool_action(description="Send a Slack message")
    async def send_message(self, params: SlackMessageRequest) -> SlackMessageResponse:
        """Send a message via Slack API"""
        try:
            response = await self.client.request(
                method=HttpMethod.POST,
                endpoint=API_ENDPOINT,
                response_model=SlackMessageResponse,
                data=params.message_data,
                params={"token": self.config.api_token},
            )
            logger.info("Slack message sent successfully")
            return response
        except Exception as e:
            logger.error("Failed to send Slack message", error=str(e))
            raise
