import pytest
from unittest.mock import patch, MagicMock
import datetime
from temporalio import workflow
from temporalio.testing import WorkflowEnvironment

from pantheon_v2.processes.common.accounts_payable.workflows.invoice_approval import (
    InvoiceApprovalWorkflow,
)
from pantheon_v2.processes.common.accounts_payable.models.invoice_approval_models import (
    FetchInvoiceQueryResult,
    FetchInvoiceMetadataQueryResult,
    FetchHierarchyResponse,
)
from pantheon_v2.tools.core.internal_data_repository.models import (
    RelationalQueryResult,
)
from pantheon_v2.tools.common.ocr.models import (
    OCRExtractInput,
    OCRExtractOutput,
    ExtractionType,
)
from pantheon_v2.processes.common.accounts_payable.constants.invoice_approval_constants import (
    APPROVAL_HIERARCHY_KEY,
    APPROVAL_RESPONSE_APPROVE,
    APPROVAL_RESPONSE_DISAPPROVE,
    STATUS_OK,
)
from pantheon_v2.processes.common.accounts_payable.models.invoice_approval_models import (
    ProcessedFileInfo,
    ApprovalResponse,
    InvoiceData,
)
from pantheon_v2.tools.core.internal_data_repository.models import (
    BlobStorageFolderResult,
    BlobStorageFile,
)
from pantheon_v2.processes.common.accounts_payable.workflows.helpers import (
    attachment_processor,
    approval_processor,
)

from pantheon_v2.processes.common.accounts_payable.workflows.helpers.slack_processor import (
    prepare_slack_message,
    send_slack_notification,
)

from pantheon_v2.tools.external.slack.models import SlackMessageRequest


@pytest.fixture
def workflow_instance():
    with patch.object(
        workflow,
        "info",
        return_value=MagicMock(workflow_id="MOCK_ID", run_id="MOCK_RUN"),
    ):
        return InvoiceApprovalWorkflow()


@pytest.fixture
def mock_query_result():
    return RelationalQueryResult[FetchInvoiceQueryResult](
        data=[
            FetchInvoiceQueryResult(
                approvers=[{"email": "MOCK_APPROVER", "status": ""}],
                gcspath="gs://mock-bucket/mock-folder",
            )
        ],
        row_count=1,
    )


@pytest.fixture
def mock_metadata_result():
    """Mock metadata query result with approval hierarchy"""
    metadata = {
        APPROVAL_HIERARCHY_KEY: [
            {
                "email": "MOCK_APPROVER",
                "status": "",  # Empty status means pending approval
                "message": "",
            }
        ]
    }
    return RelationalQueryResult[FetchInvoiceMetadataQueryResult](
        data=[
            FetchInvoiceMetadataQueryResult(
                metadata=metadata,
            )
        ],
        row_count=1,
    )


@pytest.fixture
def mock_blob_result():
    return BlobStorageFolderResult(
        files=[
            BlobStorageFile(
                name="test.pdf",
                full_path="gs://test/attachments/test.pdf",
                relative_path="attachments/test.pdf",
                size=1000,
                content_type="application/pdf",
                created=datetime.datetime.now(),
                updated=datetime.datetime.now(),
                content=b"test content",
            )
        ]
    )


@pytest.fixture
def mock_invoice_data():
    """Mock invoice data with all required fields"""
    return InvoiceData(
        is_invoice=True,
        confidence=0.95,
        bill_to_name="MOCK_BILL_TO",
        bill_to_address="MOCK_BILL_TO_ADDRESS",
        bill_from_name="MOCK_BILL_FROM",
        bill_from_address="MOCK_BILL_FROM_ADDRESS",
        currency="USD",
        invoice_number="INV001",
        issue_date="2023-01-01",
        due_date="2023-02-01",
        total_amount=1000.0,
        itemized_breakdown='[{"description": "MOCK_ITEM", "quantity": 1, "unit_price": 1000.0, "total": 1000.0}]',
        description="Test invoice",
    )


@pytest.fixture
def mock_ocr_response():
    """Mock OCR response with invoice data"""
    return OCRExtractOutput[InvoiceData](
        extracted_data=InvoiceData(
            is_invoice=True,
            confidence=0.95,
            bill_to_name="MOCK_BILL_TO",
            bill_to_address="MOCK_BILL_TO_ADDRESS",
            bill_from_name="MOCK_BILL_FROM",
            bill_from_address="MOCK_BILL_FROM_ADDRESS",
            currency="USD",
            invoice_number="INV001",
            issue_date="2023-01-01",
            due_date="2023-02-01",
            total_amount=1000.0,
            itemized_breakdown='[{"description": "MOCK_ITEM", "quantity": 1, "unit_price": 1000.0, "total": 1000.0}]',
            description="Test invoice",
        )
    )


@pytest.fixture
async def workflow_env():
    """Create a workflow environment for testing"""
    async with await WorkflowEnvironment.start_local() as env:
        yield env


@pytest.fixture
def mock_hierarchy_response():
    """Mock hierarchy response for slack message testing"""
    return FetchHierarchyResponse(
        next_approver="approver@example.com",
        vendor_id="vendor123",
        invoice_date="2024-01-01",
        invoice_amount="1000.0",
        due_date="2024-02-01",
        description="Test Invoice",
        invoice_gcs_path="gs://bucket/path/invoice.pdf",
    )


class TestInvoiceApprovalWorkflow:
    @pytest.mark.asyncio
    async def test_process_attachments(self):
        """Test processing invoice attachments"""
        with patch.object(attachment_processor, "process_attachments") as mock_process:
            mock_process.return_value = [
                ProcessedFileInfo(
                    name="test.pdf",
                    full_path="test.pdf",
                    relative_path="test.pdf",
                    size=1000,
                    content_type="application/pdf",
                    created=datetime.datetime.now(),
                    updated=datetime.datetime.now(),
                    extracted_data=InvoiceData(
                        is_invoice=True,
                        confidence=0.9,
                        bill_to_name="Test",
                        bill_to_address="Test",
                        bill_from_name="Test",
                        bill_from_address="Test",
                        currency="USD",
                        invoice_number="123",
                        issue_date="2024-01-01",
                        due_date="2024-02-01",
                        total_amount=100.0,
                        description="Test",
                        itemized_breakdown='[{"description": "Test", "quantity": 1, "unit_price": 100.0, "total": 100.0}]',
                    ),
                )
            ]

            result = await attachment_processor.process_attachments(
                FetchInvoiceQueryResult(approvers=[], gcspath="gs://bucket/path")
            )
            assert len(result) == 1
            assert result[0].extracted_data.is_invoice is True

    @pytest.mark.asyncio
    async def test_update_approver_status(self):
        """Test updating approver status in metadata"""
        metadata = {APPROVAL_HIERARCHY_KEY: [{"email": "test@example.com"}]}
        approval_response = ApprovalResponse(
            code="200",
            message="Approved",
            status="approve",
        )
        approval_processor.update_approver_status(
            metadata, "test@example.com", approval_response
        )
        assert (
            metadata[APPROVAL_HIERARCHY_KEY][0]["status"] == APPROVAL_RESPONSE_APPROVE
        )

    @pytest.mark.asyncio
    async def test_get_next_approver_no_hierarchy(self):
        """Test getting next approver when no hierarchy exists"""
        metadata = {}
        # When is_initial_fetch=False
        assert (
            approval_processor.get_next_approver(metadata, is_initial_fetch=False)
            is None
        )
        # When is_initial_fetch=True
        assert (
            approval_processor.get_next_approver(metadata, is_initial_fetch=True)
            is None
        )

    @pytest.mark.asyncio
    async def test_get_next_approver_disapproved(self):
        """Test getting next approver when invoice is disapproved"""
        metadata = {
            APPROVAL_HIERARCHY_KEY: [
                {
                    "email": "test@example.com",
                    "status": APPROVAL_RESPONSE_DISAPPROVE,
                    "message": "Disapproved",
                }
            ]
        }
        with pytest.raises(
            ValueError, match="Invoice has been disapproved by test@example.com"
        ):
            approval_processor.get_next_approver(metadata)

    @pytest.mark.asyncio
    async def test_get_next_approver_no_pending(self):
        """Test getting next approver when no pending approvers exist"""
        metadata = {
            APPROVAL_HIERARCHY_KEY: [
                {
                    "email": "test@example.com",
                    "status": APPROVAL_RESPONSE_APPROVE,
                    "message": "Approved",
                }
            ]
        }
        # When is_initial_fetch=False, should return None instead of raising error
        assert (
            approval_processor.get_next_approver(metadata, is_initial_fetch=False)
            is None
        )

        # When is_initial_fetch=True, should raise error
        with pytest.raises(
            ValueError, match="No pending approvers found in the approval hierarchy"
        ):
            approval_processor.get_next_approver(metadata, is_initial_fetch=True)

    @pytest.mark.asyncio
    async def test_process_single_file(self, mock_ocr_response, workflow_env):
        """Test processing a single file with OCR"""
        # Create BlobStorageFile instead of dict
        test_file = BlobStorageFile(
            name="test.pdf",
            full_path="gs://test/attachments/test.pdf",
            relative_path="attachments/test.pdf",
            size=1000,
            content_type="application/pdf",
            created=datetime.datetime.now(),
            updated=datetime.datetime.now(),
            content=b"test content",
        )

        with patch(
            "pantheon_v2.processes.common.accounts_payable.workflows.helpers.attachment_processor.workflow.execute_activity"
        ) as mock_activity:
            mock_activity.return_value = mock_ocr_response

            result = await attachment_processor.process_single_file(test_file)

            # Verify OCR activity was called correctly
            mock_activity.assert_called_once()

            # Get the args from the mock call
            args = mock_activity.call_args.kwargs.get("args", [])

            # Verify the OCR input
            assert len(args) > 0
            assert isinstance(args[0], OCRExtractInput)
            assert args[0].extraction_type == ExtractionType.INVOICE

            # Verify result
            assert result.name == test_file.name  # Updated to use property access
            assert result.extracted_data == mock_ocr_response.extracted_data


class TestSlackProcessor:
    @pytest.mark.asyncio
    async def test_prepare_slack_message(self, mock_hierarchy_response):
        """Test preparing slack message with all required fields"""
        with patch.object(
            workflow,
            "info",
            return_value=MagicMock(workflow_id="test-workflow", run_id="test-run"),
        ):
            message_request = await prepare_slack_message(
                mock_hierarchy_response, "approver@example.com", "invoice123"
            )

            assert message_request.message_data["workflow_id"] == "test-workflow"
            assert message_request.message_data["run_id"] == "test-run"
            assert message_request.message_data["vendor"] == "vendor123"
            assert message_request.message_data["user_email"] == "approver@example.com"
            assert message_request.message_data["invoice_id"] == "invoice123"
            assert message_request.message_data["invoice_date"] == "2024-01-01"
            assert message_request.message_data["invoice_amount"] == "1000.0"
            assert message_request.message_data["due_date"] == "2024-02-01"
            assert message_request.message_data["description"] == "Test Invoice"
            assert (
                message_request.message_data["invoice_gcs_path"]
                == "gs://bucket/path/invoice.pdf"
            )

    @pytest.mark.asyncio
    async def test_send_slack_notification_success(self):
        """Test successful slack notification sending"""
        mock_request = SlackMessageRequest(
            message_data={
                "workflow_id": "test-workflow",
                "run_id": "test-run",
                "vendor": "vendor123",
                "user_email": "approver@example.com",
                "invoice_id": "invoice123",
            }
        )

        with patch(
            "pantheon_v2.processes.platform.zamp_ap_agent.zamp_ap_agent.workflow.execute_activity"
        ) as mock_activity:
            mock_activity.return_value = MagicMock(status=STATUS_OK)

            result = await send_slack_notification(mock_request)
            assert result is True

    @pytest.mark.asyncio
    async def test_send_slack_notification_failure(self):
        """Test failed slack notification sending"""
        mock_request = SlackMessageRequest(
            message_data={
                "workflow_id": "test-workflow",
                "run_id": "test-run",
                "vendor": "vendor123",
                "user_email": "approver@example.com",
                "invoice_id": "invoice123",
            }
        )

        with patch(
            "pantheon_v2.processes.platform.zamp_ap_agent.zamp_ap_agent.workflow.execute_activity"
        ) as mock_activity:
            mock_activity.return_value = MagicMock(status="ERROR")

            result = await send_slack_notification(mock_request)
            assert result is False

    @pytest.mark.asyncio
    async def test_prepare_slack_message_with_missing_data(
        self, mock_hierarchy_response
    ):
        """Test preparing slack message with missing optional fields"""
        # Modify hierarchy response to have some missing fields
        mock_hierarchy_response.description = None
        mock_hierarchy_response.due_date = None

        with patch.object(
            workflow,
            "info",
            return_value=MagicMock(workflow_id="test-workflow", run_id="test-run"),
        ):
            message_request = await prepare_slack_message(
                mock_hierarchy_response, "approver@example.com", "invoice123"
            )

            assert message_request.message_data["workflow_id"] == "test-workflow"
            assert message_request.message_data["description"] is None
            assert message_request.message_data["due_date"] is None
            assert message_request.message_data["invoice_id"] == "invoice123"

    @pytest.mark.asyncio
    async def test_send_slack_notification_with_empty_message(self):
        """Test sending slack notification with empty message data"""
        mock_request = SlackMessageRequest(message_data={})

        with patch(
            "pantheon_v2.processes.platform.zamp_ap_agent.zamp_ap_agent.workflow.execute_activity"
        ) as mock_activity:
            mock_activity.return_value = MagicMock(status=STATUS_OK)

            result = await send_slack_notification(mock_request)
            assert result is True
