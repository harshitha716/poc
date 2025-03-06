from temporalio import workflow
from pantheon_v2.tools.external.slack.models import SlackMessageRequest
from pantheon_v2.tools.external.slack.activities import send_slack_message
from pantheon_v2.tools.external.slack.config import SlackConfig
from pantheon_v2.settings.settings import Settings
from pantheon_v2.processes.common.accounts_payable.models.invoice_approval_models import (
    FetchHierarchyResponse,
)
from pantheon_v2.processes.common.accounts_payable.constants.invoice_approval_constants import (
    SLACK_MESSAGE_TIMEOUT,
    STATUS_OK,
)


async def prepare_slack_message(
    hierarchy: FetchHierarchyResponse, current_approver: str, invoice_id: str
) -> SlackMessageRequest:
    workflow_info = workflow.info()
    return SlackMessageRequest(
        message_data={
            "workflow_id": workflow_info.workflow_id,
            "run_id": workflow_info.run_id,
            "vendor": hierarchy.vendor_id,
            "user_email": current_approver,
            "invoice_id": invoice_id,
            "invoice_date": hierarchy.invoice_date,
            "invoice_amount": str(hierarchy.invoice_amount),
            "due_date": hierarchy.due_date,
            "description": hierarchy.description,
            "invoice_gcs_path": hierarchy.invoice_gcs_path,
        },
    )


async def send_slack_notification(request: SlackMessageRequest) -> bool:
    config = SlackConfig(
        api_base_url=Settings.WINDMILL_SEND_SLACK_MESSAGE_API_URL,
        api_token=Settings.WINDMILL_SEND_SLACK_MESSAGE_API_TOKEN,
    )

    result = await workflow.execute_activity(
        send_slack_message,
        args=[config, request],
        start_to_close_timeout=SLACK_MESSAGE_TIMEOUT,
    )
    return result.status == STATUS_OK
