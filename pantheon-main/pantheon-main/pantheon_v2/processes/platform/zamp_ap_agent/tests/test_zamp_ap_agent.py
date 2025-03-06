import pytest
from unittest.mock import patch, MagicMock
import datetime
import uuid
import base64
from temporalio import workflow
from temporalio.testing import WorkflowEnvironment

from pantheon_v2.processes.platform.zamp_ap_agent.zamp_ap_agent import (
    ZampAPAgentWorkflow,
)
from pantheon_v2.processes.platform.zamp_ap_agent.constants.constants import (
    STATUS_UNPROCESSED,
    STATUS_PROCESSED,
)
from pantheon_v2.tools.external.gmail.models import (
    GmailResponse,
    GmailMessage,
)
from pantheon_v2.tools.core.internal_data_repository.models import (
    RelationalQueryResult,
    BlobStorageUploadResult,
)
from pantheon_v2.processes.platform.zamp_ap_agent.models.models import (
    ProcessedEmailQueryResult,
    EmailByIdAndStatusQueryResult,
    VendorByEmailQueryResult,
    ZampAPAgentWorkflowInput,
)
from pantheon_v2.tools.common.email_parser.models import (
    ParsedEmail,
    Attachment,
    EmailAddress,
)


@pytest.fixture
def workflow_instance():
    with patch.object(
        workflow,
        "info",
        return_value=MagicMock(workflow_id="MOCK_ID", run_id="MOCK_RUN"),
    ):
        return ZampAPAgentWorkflow()


@pytest.fixture
def mock_gmail_response():
    """Mock Gmail response with messages"""
    return GmailResponse(
        messages=[
            GmailMessage(
                id="msg1",
                thread_id="thread1",
                label_ids=["INBOX"],
                snippet="Test email",
                history_id="123",
                internal_date=1234567890,
                payload=None,
                size_estimate=1000,
                raw=None,
                date=datetime.datetime.now(),
                subject="Test Invoice",
                sender="vendor@example.com",
                recipient="ap@zamp.finance",
                body="Test body",
            ),
            GmailMessage(
                id="msg2",
                thread_id="thread2",
                label_ids=["INBOX"],
                snippet="Another test email",
                history_id="124",
                internal_date=1234567891,
                payload=None,
                size_estimate=1000,
                raw=None,
                date=datetime.datetime.now(),
                subject="Another Invoice",
                sender="another@example.com",
                recipient="ap@zamp.finance",
                body="Another test body",
            ),
        ],
        next_page_token=None,
        result_size_estimate=2,
    )


@pytest.fixture
def mock_processed_emails():
    """Mock processed emails query result"""
    return RelationalQueryResult[ProcessedEmailQueryResult](
        data=[
            ProcessedEmailQueryResult(message_id="msg2"),
        ],
        row_count=1,
    )


@pytest.fixture
def mock_unprocessed_emails():
    """Mock unprocessed emails query result"""
    return RelationalQueryResult[EmailByIdAndStatusQueryResult](
        data=[
            EmailByIdAndStatusQueryResult(
                id=uuid.uuid4(),
                message_id="msg1",
                subject="Test Invoice",
                sender="vendor@example.com",
                received_at=datetime.datetime.now(),
                storage_path="",
                status=STATUS_UNPROCESSED,
                created_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now(),
            ),
        ],
        row_count=1,
    )


@pytest.fixture
def mock_vendor_result():
    """Mock vendor query result"""
    return RelationalQueryResult[VendorByEmailQueryResult](
        data=[
            VendorByEmailQueryResult(
                id="vendor1",
                name="Test Vendor",
                email="vendor@example.com",
            ),
        ],
        row_count=1,
    )


@pytest.fixture
def mock_parsed_email():
    """Mock parsed email result"""
    return ParsedEmail(
        subject="Test Invoice",
        **{"from": EmailAddress(name="Test Vendor", email="vendor@example.com")},
        to=[EmailAddress(name="Zamp Finance", email="ap@zamp.finance")],
        cc=[],
        date=datetime.datetime.now().isoformat(),
        body_plain="Test email body",
        body_html="<p>Test email body</p>",
        attachments=[
            Attachment(
                filename="invoice.pdf",
                content=base64.b64encode(b"test pdf content").decode("utf-8"),
                content_type="application/pdf",
                content_disposition="attachment",
                size=len(b"test pdf content"),
            )
        ],
    )


@pytest.fixture
async def workflow_env():
    """Create a workflow environment for testing"""
    async with await WorkflowEnvironment.start_local() as env:
        yield env


class TestZampAPAgentWorkflow:
    @pytest.mark.asyncio
    async def test_fetch_new_emails(self, workflow_instance, mock_gmail_response):
        """Test fetching new emails from Gmail"""
        with patch(
            "pantheon_v2.processes.platform.zamp_ap_agent.zamp_ap_agent.workflow.execute_activity"
        ) as mock_activity:
            mock_activity.return_value = mock_gmail_response

            result = await workflow_instance._fetch_new_emails("6h")

            # Verify activity was called
            mock_activity.assert_called_once()

            # Verify result
            assert result == mock_gmail_response
            assert len(result.messages) == 2
            assert result.messages[0].id == "msg1"
            assert result.messages[1].id == "msg2"

    @pytest.mark.asyncio
    async def test_filter_emails(
        self, workflow_instance, mock_gmail_response, mock_processed_emails
    ):
        """Test filtering out already processed emails"""
        with patch(
            "pantheon_v2.processes.platform.zamp_ap_agent.zamp_ap_agent.workflow.execute_activity"
        ) as mock_activity:
            mock_activity.return_value = mock_processed_emails

            result = await workflow_instance._filter_emails(mock_gmail_response)

            # Verify activity was called
            mock_activity.assert_called_once()

            # Verify result - should only contain msg1 as msg2 is already processed
            assert len(result) == 1
            assert result[0].id == "msg1"

    @pytest.mark.asyncio
    async def test_process_and_store_email_content(
        self, workflow_instance, mock_unprocessed_emails
    ):
        """Test processing and storing email content"""
        with patch(
            "pantheon_v2.processes.platform.zamp_ap_agent.zamp_ap_agent.workflow.execute_activity"
        ) as mock_activity, patch.object(
            workflow_instance, "_process_single_email"
        ) as mock_process_single:
            mock_activity.return_value = mock_unprocessed_emails

            await workflow_instance._process_and_store_email_content(["email1"])

            # Verify activity was called to fetch unprocessed emails
            mock_activity.assert_called_once()

            # Verify _process_single_email was called for each unprocessed email
            mock_process_single.assert_called_once_with(mock_unprocessed_emails.data[0])

    @pytest.mark.asyncio
    async def test_fetch_and_store_eml(self, workflow_instance):
        """Test fetching and storing EML content"""
        eml_data = b"test eml content"

        with patch(
            "pantheon_v2.processes.platform.zamp_ap_agent.zamp_ap_agent.workflow.execute_activity"
        ) as mock_activity:
            # Configure mock to return different values on each call
            mock_activity.side_effect = [
                eml_data,  # First call returns EML data
                BlobStorageUploadResult(
                    metadata={"content-type": "message/rfc822"},
                    gcs_url="gs://bucket/path",
                    https_url="https://storage.googleapis.com/bucket/path",
                ),  # Second call returns upload result
            ]

            result_data, result_folder = await workflow_instance._fetch_and_store_eml(
                "msg1"
            )

            # Verify activity was called twice (get_message_eml and upload_internal_blob_storage)
            assert mock_activity.call_count == 2

            # Verify results
            assert result_data == eml_data
            assert result_folder == "emails/msg1"

    @pytest.mark.asyncio
    async def test_handle_vendor_and_invoice(
        self, workflow_instance, mock_parsed_email, mock_vendor_result
    ):
        """Test handling vendor and invoice creation for whitelisted vendor"""
        with patch.object(
            workflow_instance, "_get_vendor_by_email"
        ) as mock_get_vendor, patch.object(
            workflow_instance, "_create_invoice_and_workflow"
        ) as mock_create_invoice, patch.object(
            workflow_instance, "_build_email_update_params"
        ) as mock_build_params, patch(
            "pantheon_v2.processes.platform.zamp_ap_agent.zamp_ap_agent.workflow.execute_activity"
        ) as mock_activity, patch(
            "pantheon_v2.processes.platform.zamp_ap_agent.zamp_ap_agent.Settings",
            AP_AGENT_EMAILS_BUCKET="ap-agent-emails-bucket",
        ):
            # Configure mocks
            mock_get_vendor.return_value = mock_vendor_result
            mock_build_params.return_value = MagicMock()

            # Create a proper EmailAddress object for from_
            mock_parsed_email.from_ = EmailAddress(
                name="Test Vendor", email="vendor@example.com"
            )

            await workflow_instance._handle_vendor_and_invoice(
                "msg1", mock_parsed_email, "emails/msg1"
            )

            # Verify vendor was checked
            mock_get_vendor.assert_called_once_with("vendor@example.com")

            # Verify invoice workflow was created for whitelisted vendor
            mock_create_invoice.assert_called_once_with(
                "vendor1", "emails/msg1/attachments"
            )

            # Verify email status was updated to PROCESSED
            mock_build_params.assert_called_once_with(
                "msg1", "gs://ap-agent-emails-bucket/emails/msg1", STATUS_PROCESSED
            )

            # Verify update activity was called
            mock_activity.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_vendor_not_found(self, workflow_instance, mock_parsed_email):
        """Test handling case where no vendor is found for the email"""
        with patch.object(
            workflow_instance, "_get_vendor_by_email"
        ) as mock_get_vendor, patch.object(
            workflow_instance, "_build_email_update_params"
        ) as mock_build_params, patch(
            "pantheon_v2.processes.platform.zamp_ap_agent.zamp_ap_agent.workflow.execute_activity"
        ) as mock_activity, patch(
            "pantheon_v2.processes.platform.zamp_ap_agent.zamp_ap_agent.Settings",
            AP_AGENT_EMAILS_BUCKET="ap-agent-emails-bucket",
        ):
            # Configure mocks to return empty vendor result (no vendor found)
            mock_get_vendor.return_value = RelationalQueryResult[
                VendorByEmailQueryResult
            ](data=[], row_count=0)
            mock_build_params.return_value = MagicMock()

            # Create a proper EmailAddress object for from_
            mock_parsed_email.from_ = EmailAddress(
                name="Unknown Vendor", email="unknown@example.com"
            )

            await workflow_instance._handle_vendor_and_invoice(
                "msg1", mock_parsed_email, "emails/msg1"
            )

            # Verify vendor was checked
            mock_get_vendor.assert_called_once_with("unknown@example.com")

            # Verify email status was updated to UNPROCESSED for non-whitelisted vendor
            mock_build_params.assert_called_once_with(
                "msg1", "gs://ap-agent-emails-bucket/emails/msg1", STATUS_UNPROCESSED
            )

            # Verify update activity was called
            mock_activity.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_workflow(self, workflow_instance, mock_gmail_response):
        """Test the main execute method of the workflow"""
        with patch.object(
            workflow_instance, "_fetch_new_emails"
        ) as mock_fetch_emails, patch.object(
            workflow_instance, "_filter_emails"
        ) as mock_filter_emails, patch.object(
            workflow_instance, "_process_and_store_email_content"
        ) as mock_process_emails, patch.object(
            workflow_instance, "_persist_emails"
        ) as mock_persist_emails:
            # Configure mocks
            mock_fetch_emails.return_value = mock_gmail_response
            mock_filter_emails.return_value = [
                mock_gmail_response.messages[0]
            ]  # Only return one filtered email
            mock_persist_emails.return_value = ["msg1"]  # Return message ID

            # Run the workflow
            await workflow_instance.execute(ZampAPAgentWorkflowInput(newer_than="6h"))

            # Verify all methods were called in sequence
            mock_fetch_emails.assert_called_once()
            mock_filter_emails.assert_called_once_with(mock_gmail_response)
            mock_persist_emails.assert_called_once_with(
                [mock_gmail_response.messages[0]]
            )
            mock_process_emails.assert_called_once_with(["msg1"])
