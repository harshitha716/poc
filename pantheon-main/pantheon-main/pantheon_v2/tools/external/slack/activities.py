from pantheon_v2.tools.external.slack.models import (
    SlackMessageRequest,
    SlackMessageResponse,
)
from pantheon_v2.tools.external.slack.config import SlackConfig

from pantheon_v2.tools.external.slack.tool import SlackTool
from pantheon_v2.tools.core.activity_registry import ActivityRegistry


@ActivityRegistry.register_activity("Send a message via Slack")
async def send_slack_message(
    config: SlackConfig, request: SlackMessageRequest
) -> SlackMessageResponse:
    tool = SlackTool(config)
    await tool.initialize()
    return await tool.send_message(request)
