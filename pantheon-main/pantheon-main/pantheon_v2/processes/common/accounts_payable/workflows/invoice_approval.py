from pantheon_v2.processes.core.registry import WorkflowRegistry
from temporalio import workflow
import asyncio
import datetime
from pantheon_v2.processes.common.accounts_payable.constants.invoice_approval_constants import (
    INVOICE_TABLE,
)

with workflow.unsafe.imports_passed_through():
    import structlog
    from pantheon_v2.processes.common.accounts_payable.models.invoice_approval_models import (
        APInvoiceApprovalWorkflowInput,
        APInvoiceApprovalWorkflowOutput,
        ApprovalState,
        FetchHierarchyResponse,
        FetchHierarchyQueryResult,
        ApprovalResponse,
        ApprovalActivityResponse,
    )
    from pantheon_v2.tools.core.internal_data_repository.models import (
        RelationalQueryParams,
        RelationalUpdateParams,
    )
    from pantheon_v2.tools.core.internal_data_repository.activities import (
        query_internal_relational_data,
        update_internal_relational_data,
    )
    from pantheon_v2.processes.common.accounts_payable.constants.invoice_approval_constants import (
        FETCH_HIERARCHY_QUERY,
        FETCH_HIERARCHY_TIMEOUT,
        STATUS_OK,
        STATUS_ERROR,
        INVOICE_STATUS_APPROVED,
        INVOICE_STATUS_DISAPPROVED,
        INVOICE_STATUS_PROCESSING,
        INVOICE_STATUS_PENDING_APPROVAL,
        APPROVAL_RESPONSE_DISAPPROVE,
        APPROVAL_RESPONSE_APPROVE,
        INVOICE_APPROVED_MESSAGE,
        INVOICE_DISAPPROVED_MESSAGE,
    )
    from pantheon_v2.processes.common.accounts_payable.workflows.helpers.approval_processor import (
        fetch_invoice_metadata,
        get_next_approver,
        update_approver_status,
        update_metadata_in_db,
    )
    from pantheon_v2.processes.common.accounts_payable.workflows.helpers.attachment_processor import (
        fetch_invoice_data,
        process_attachments,
    )
    from pantheon_v2.processes.common.accounts_payable.workflows.helpers.invoice_processor import (
        filter_invoice_files,
        prepare_metadata,
        update_invoice,
    )
    from pantheon_v2.processes.common.accounts_payable.workflows.helpers.slack_processor import (
        prepare_slack_message,
        send_slack_notification,
    )

    logger = structlog.get_logger(__name__)


@WorkflowRegistry.register_workflow_defn(
    "Workflow that processes an invoice for approval",
    labels=["accounts_payable"],
)
class InvoiceApprovalWorkflow:
    def __init__(self):
        self._pending_responses = asyncio.Queue()
        self._state = ApprovalState(
            current_approver="", approval_chain=[], current_level=0, is_completed=False
        )

    @WorkflowRegistry.register_workflow_signal(name="received_slack_response")
    async def handle_slack_response(self, input: ApprovalResponse) -> None:
        await self._pending_responses.put(input)

    @WorkflowRegistry.register_workflow_run
    async def execute(
        self, params: APInvoiceApprovalWorkflowInput
    ) -> APInvoiceApprovalWorkflowOutput:
        # Step 1: Update status to processing and process attachments
        await self._update_invoice_status(params.invoice_id, INVOICE_STATUS_PROCESSING)
        hierarchy = await self._fetch_initial_data(params.invoice_id)

        # Step 2: Update status to pending approval
        await self._update_invoice_status(
            params.invoice_id, INVOICE_STATUS_PENDING_APPROVAL
        )
        current_approver = hierarchy.next_approver

        # Step 3: Send Slack notification to the first approver
        message_details = await prepare_slack_message(
            hierarchy, current_approver, params.invoice_id
        )
        if not await send_slack_notification(message_details):
            return APInvoiceApprovalWorkflowOutput(
                invoice_id=params.invoice_id, status=STATUS_ERROR
            )

        # Step 4: Process approval chain
        while True:
            await workflow.wait_condition(lambda: not self._pending_responses.empty())
            response = self._pending_responses.get_nowait()

            approval_result = await self._process_approval(
                response, current_approver, params.invoice_id
            )

            if not approval_result.should_continue:
                status = (
                    INVOICE_STATUS_DISAPPROVED
                    if approval_result.status == "disapprove"
                    else INVOICE_STATUS_APPROVED
                )
                await self._update_invoice_status(params.invoice_id, status)
                break

            if approval_result.next_approver:
                current_approver = approval_result.next_approver
                message_details.user_email = current_approver

                if not await send_slack_notification(message_details):
                    break

                self._pending_responses = asyncio.Queue()
            else:
                break

        return APInvoiceApprovalWorkflowOutput(
            invoice_id=params.invoice_id, status=STATUS_OK
        )

    async def _update_invoice_status(self, invoice_id: str, status: str) -> None:
        """Update the invoice status in the database"""
        update_params = RelationalUpdateParams(
            table=INVOICE_TABLE,
            data={"status": status},
            where={"id": invoice_id},
        )

        await workflow.execute_activity(
            update_internal_relational_data,
            args=[update_params],
            start_to_close_timeout=datetime.timedelta(seconds=30),
        )

    async def _fetch_initial_data(self, invoice_id: str) -> FetchHierarchyResponse:
        # Process attachments first
        await self._process_invoice_attachments(invoice_id)

        query_params = RelationalQueryParams(
            query=FETCH_HIERARCHY_QUERY,
            parameters={"invoice_id": invoice_id},
            output_model=FetchHierarchyQueryResult,
        )

        result = await workflow.execute_activity(
            query_internal_relational_data,
            args=[query_params],
            start_to_close_timeout=FETCH_HIERARCHY_TIMEOUT,
        )

        if not result.data:
            raise ValueError(f"No data found for invoice_id: {invoice_id}")

        row_data = result.data[0]

        # Validate data
        approvers_data = row_data.approvers
        vendor_id = row_data.vendorid

        if not approvers_data:
            raise ValueError("No approvers data found")

        if not vendor_id:
            raise ValueError("Vendor ID not found")

        next_approver_email = get_next_approver(
            row_data.metadata, is_initial_fetch=True
        )

        return FetchHierarchyResponse(
            next_approver=next_approver_email,
            vendor_id=vendor_id,
            invoice_date=row_data.invoicedate,
            invoice_amount=row_data.amount,
            due_date=row_data.duedate,
            description=row_data.description,
            invoice_gcs_path=row_data.invoice_gcs_path,
        )

    async def _process_invoice_attachments(self, invoice_id: str):
        """Process invoice attachments and update invoice with extracted data"""
        invoice_data = await fetch_invoice_data(invoice_id)

        processed_files = await process_attachments(invoice_data)

        filtered_files = filter_invoice_files(processed_files)
        if not filtered_files:
            raise ValueError("No valid invoice documents found in the attachments")

        metadata = prepare_metadata(
            filtered_files[0], invoice_data.approvers, processed_files
        )
        await update_invoice(invoice_id, filtered_files[0], metadata)

    async def _process_approval(
        self, approval_response: ApprovalResponse, email: str, invoice_id: str
    ) -> ApprovalActivityResponse:
        metadata = await fetch_invoice_metadata(invoice_id)

        update_approver_status(metadata, email, approval_response)

        await update_metadata_in_db(invoice_id, metadata)

        if approval_response.status.lower() == APPROVAL_RESPONSE_DISAPPROVE:
            logger.info("Invoice has been disapproved", invoice_id=invoice_id)
            return ApprovalActivityResponse(
                next_approver=None,
                should_continue=False,
                msg=INVOICE_DISAPPROVED_MESSAGE,
                status=APPROVAL_RESPONSE_DISAPPROVE,
            )

        next_approver_email = get_next_approver(metadata)

        return ApprovalActivityResponse(
            next_approver=next_approver_email,
            should_continue=next_approver_email is not None,
            msg=INVOICE_APPROVED_MESSAGE,
            status=APPROVAL_RESPONSE_APPROVE,
        )
