from temporalio import workflow
from typing import List, Tuple
from datetime import UTC
from io import BytesIO

with workflow.unsafe.imports_passed_through():
    import datetime
    from uuid import UUID
    from pantheon_v2.processes.core.registry import WorkflowRegistry
    from pantheon_v2.tools.external.gmail.activities import search_messages
    from pantheon_v2.tools.external.gmail.models import (
        GmailSearchParams,
        GmailResponse,
        GmailMessage,
    )
    from pantheon_v2.settings.settings import Settings
    from pantheon_v2.tools.core.internal_data_repository.models import (
        RelationalQueryParams,
        RelationalInsertParams,
        RelationalUpdateParams,
        BlobStorageUploadParams,
    )
    from pantheon_v2.tools.core.internal_data_repository.activities import (
        query_internal_relational_data,
        insert_internal_relational_data,
        update_internal_relational_data,
        upload_internal_blob_storage,
    )
    from pantheon_v2.tools.common.code_executor.activities import execute_code
    from pantheon_v2.processes.platform.zamp_ap_agent.constants.constants import (
        ZAMPAPAGENTEMAILS,
        STATUS_UNPROCESSED,
        STATUS_PROCESSED,
        VENDOR_BY_EMAIL_QUERY,
        QUERY_SELECT_MESSAGE_IDS,
        QUERY_SELECT_EMAILS_BY_IDS_AND_STATUS,
        EMAIL_SEARCH_CONFIG,
    )
    from pantheon_v2.processes.platform.zamp_ap_agent.models.models import (
        ZampAPAgentWorkflowInput,
        ProcessedEmailQueryResult,
        EmailByIdAndStatusQueryResult,
        VendorByEmailQueryResult,
        ZampApAgentEmailSchema,
    )
    from pantheon_v2.tools.external.gmail.activities import get_message_eml
    from pantheon_v2.tools.external.gmail.models import GmailGetMessageParams
    from pantheon_v2.tools.external.gmail.config import GMAIL_CONFIG
    from pantheon_v2.tools.common.email_parser.activities import parse_email
    from pantheon_v2.tools.common.email_parser.models import (
        ParseEmailParams,
        ParsedEmail,
        Attachment,
    )
    from pantheon_v2.tools.common.email_parser.config import EmailParserConfig
    import structlog
    from pantheon_v2.processes.common.accounts_payable.workflows.invoice_approval import (
        InvoiceApprovalWorkflow,
    )
    from pantheon_v2.processes.common.accounts_payable.models.invoice_approval_models import (
        APInvoiceApprovalWorkflowInput,
        ZampApAgentInvoicesSchema,
    )
    from pantheon_v2.processes.common.accounts_payable.constants.invoice_approval_constants import (
        INVOICE_TABLE,
        INVOICE_STATUS_UNPROCESSED,
    )
    from pantheon_v2.tools.common.code_executor.models import ExecuteCodeParams
    from pantheon_v2.tools.common.code_executor.config import CodeExecutorConfig
    from pantheon_v2.utils.type_utils import get_fqn
    from pantheon_v2.utils.uuid_utils import generate_random_uuid
    from pantheon_v2.utils.datetime_utils import get_current_time

    logger = structlog.get_logger(__name__)


@WorkflowRegistry.register_workflow_defn(
    "Workflow that processes vendor emails received on Zamp Account",
    labels=["zamp"],
)
class ZampAPAgentWorkflow:
    @WorkflowRegistry.register_workflow_run
    async def execute(self, params: ZampAPAgentWorkflowInput):
        # Step 1: Fetch emails from Gmail newer than specified time
        fetched_emails = await self._fetch_new_emails(params.newer_than)
        if not fetched_emails.messages:
            logger.info("No new emails found")
            return

        # Step 2: Filter out already processed emails
        unprocessed_emails = await self._filter_emails(fetched_emails)
        if not unprocessed_emails:
            logger.info("No unprocessed emails found")
            return

        # Step 3: Save new emails to database
        email_uuids = await self._persist_emails(unprocessed_emails)

        # Step 4: Process and store EML content
        await self._process_and_store_email_content(email_uuids)

    async def _fetch_new_emails(self, newer_than: str) -> GmailResponse:
        return await workflow.execute_activity(
            search_messages,
            args=[
                GMAIL_CONFIG,
                GmailSearchParams(
                    query=f"list:{EMAIL_SEARCH_CONFIG['LIST_ADDRESS']} newer_than:{newer_than}",
                    max_results=EMAIL_SEARCH_CONFIG["MAX_RESULTS"],
                    include_body=EMAIL_SEARCH_CONFIG["INCLUDE_BODY"],
                ),
            ],
            start_to_close_timeout=datetime.timedelta(minutes=60),
        )

    async def _filter_emails(self, gmail_response: GmailResponse) -> List[GmailMessage]:
        message_ids = []
        for message in gmail_response.messages:
            message_ids.append(message.id)

        processed_emails = await workflow.execute_activity(
            query_internal_relational_data,
            args=[
                RelationalQueryParams(
                    query=QUERY_SELECT_MESSAGE_IDS,
                    parameters={"message_ids": message_ids},
                    output_model=ProcessedEmailQueryResult,
                )
            ],
            start_to_close_timeout=datetime.timedelta(seconds=30),
        )

        processed_message_ids = [row.message_id for row in processed_emails.data]
        unprocessed_emails = [
            email
            for email in gmail_response.messages
            if email.id not in processed_message_ids
        ]

        return unprocessed_emails

    async def _get_email_records_and_ids(self, unprocessed_emails: List[GmailMessage]):
        result = await workflow.execute_activity(
            execute_code,
            args=[
                CodeExecutorConfig(timeout_seconds=10),
                ExecuteCodeParams(
                    function=get_fqn(construct_email_records),
                    args=(unprocessed_emails,),
                ),
            ],
            start_to_close_timeout=datetime.timedelta(seconds=10),
        )

        return result.result

    async def _persist_emails(
        self, unprocessed_emails: List[GmailMessage]
    ) -> List[str]:
        email_records, unprocessed_emails_ids = await self._get_email_records_and_ids(
            unprocessed_emails
        )

        await workflow.execute_activity(
            insert_internal_relational_data,
            args=[
                RelationalInsertParams(
                    table=ZAMPAPAGENTEMAILS,
                    data=email_records,
                )
            ],
            start_to_close_timeout=datetime.timedelta(seconds=60),
        )

        return unprocessed_emails_ids

    async def _process_and_store_email_content(self, email_uuids: List[str]):
        """Fetch and process unprocessed emails"""
        unprocessed_emails = await self._fetch_unprocessed_emails(email_uuids)
        for unprocessed_email in unprocessed_emails.data:
            await self._process_single_email(unprocessed_email)

    async def _fetch_unprocessed_emails(self, email_uuids: List[str]):
        """Fetch emails that need processing"""
        return await workflow.execute_activity(
            query_internal_relational_data,
            args=[
                RelationalQueryParams(
                    query=QUERY_SELECT_EMAILS_BY_IDS_AND_STATUS,
                    parameters={"ids": email_uuids, "status": STATUS_UNPROCESSED},
                    output_model=EmailByIdAndStatusQueryResult,
                )
            ],
            start_to_close_timeout=datetime.timedelta(seconds=30),
        )

    async def _process_single_email(
        self, unprocessed_email: EmailByIdAndStatusQueryResult
    ):
        """Process a single email through the following steps:
        1. Fetch and store EML content
        2. Parse email and upload attachments
        3. Check vendor and process invoice if whitelisted
        """
        message_id = unprocessed_email.message_id

        # Step 1: Fetch and store EML
        eml_data, base_folder = await self._fetch_and_store_eml(message_id)

        # Step 2: Parse and store attachments
        parsed_email = await self._parse_and_store_attachments(eml_data, base_folder)

        # Step 3: Process vendor and invoice
        await self._handle_vendor_and_invoice(message_id, parsed_email, base_folder)

    async def _fetch_and_store_eml(self, message_id: str) -> Tuple[bytes, str]:
        """Fetch EML content and store it in GCS"""
        eml_data: bytes = await workflow.execute_activity(
            get_message_eml,
            args=[
                GMAIL_CONFIG,
                GmailGetMessageParams(message_id=message_id),
            ],
            start_to_close_timeout=datetime.timedelta(minutes=5),
        )

        base_folder = f"emails/{message_id}"

        await workflow.execute_activity(
            upload_internal_blob_storage,
            args=[
                BlobStorageUploadParams(
                    bucket_name=Settings.AP_AGENT_EMAILS_BUCKET,
                    file_name=f"{base_folder}/email.eml",
                    blob=BytesIO(eml_data),
                )
            ],
            start_to_close_timeout=datetime.timedelta(minutes=5),
        )

        return eml_data, base_folder

    async def _parse_and_store_attachments(
        self, eml_data: bytes, base_folder: str
    ) -> ParsedEmail:
        """Parse email and store any attachments"""
        parsed_email: ParsedEmail = await workflow.execute_activity(
            parse_email,
            args=[
                EmailParserConfig(default_encoding="utf-8", max_size=10 * 1024 * 1024),
                ParseEmailParams(
                    eml_content=eml_data.decode("utf-8"), include_attachments=True
                ),
            ],
            start_to_close_timeout=datetime.timedelta(minutes=5),
        )

        if parsed_email.attachments:
            await self._store_attachments(parsed_email.attachments, base_folder)

        return parsed_email

    async def _store_attachments(self, attachments: List[Attachment], base_folder: str):
        """Store email attachments in GCS"""
        attachments_folder = f"{base_folder}/attachments"
        for attachment in attachments:
            if attachment.content and attachment.filename:
                attachment_buffer = BytesIO(attachment.content)
                await workflow.execute_activity(
                    upload_internal_blob_storage,
                    args=[
                        BlobStorageUploadParams(
                            bucket_name=Settings.AP_AGENT_EMAILS_BUCKET,
                            file_name=f"{attachments_folder}/{attachment.filename}",
                            blob=attachment_buffer,
                        )
                    ],
                    start_to_close_timeout=datetime.timedelta(minutes=5),
                )

    async def _handle_vendor_and_invoice(
        self, message_id: str, parsed_email: ParsedEmail, base_folder: str
    ):
        """Check vendor status and handle invoice creation if whitelisted"""
        gcs_path = f"gs://{Settings.AP_AGENT_EMAILS_BUCKET}/{base_folder}"
        vendor_result = await self._get_vendor_by_email(parsed_email.from_.email)

        if vendor_result.data:
            await self._create_invoice_and_workflow(
                vendor_result.data[0].id, f"{base_folder}/attachments"
            )
            update_params = self._build_email_update_params(
                message_id, gcs_path, STATUS_PROCESSED
            )
        else:
            logger.info(
                "Skipping invoice creation for non-whitelisted vendor email",
                sender=parsed_email.from_,
                message_id=message_id,
            )
            update_params = self._build_email_update_params(
                message_id, gcs_path, STATUS_UNPROCESSED
            )

        await workflow.execute_activity(
            update_internal_relational_data,
            args=[update_params],
            start_to_close_timeout=datetime.timedelta(seconds=30),
        )

    async def _get_vendor_by_email(self, email: str):
        """Check if sender is a whitelisted vendor"""
        return await workflow.execute_activity(
            query_internal_relational_data,
            args=[
                RelationalQueryParams(
                    query=VENDOR_BY_EMAIL_QUERY,
                    parameters={"email": email},
                    output_model=VendorByEmailQueryResult,
                )
            ],
            start_to_close_timeout=datetime.timedelta(seconds=30),
        )

    async def _create_invoice_and_workflow(self, vendor_id: str, attachments_path: str):
        """Create invoice record and spawn invoice approval workflow"""
        invoice_records: List[ZampApAgentInvoicesSchema] = []
        invoice_id = await self._generate_uuid()
        invoice_records.append(
            ZampApAgentInvoicesSchema(
                id=invoice_id,
                vendorid=vendor_id,
                gcspath=f"gs://{Settings.AP_AGENT_EMAILS_BUCKET}/{attachments_path}",
                status=INVOICE_STATUS_UNPROCESSED,
            )
        )

        await workflow.execute_activity(
            insert_internal_relational_data,
            args=[
                RelationalInsertParams(
                    table=INVOICE_TABLE,
                    data=invoice_records,
                )
            ],
            start_to_close_timeout=datetime.timedelta(seconds=60),
        )

        # Spawn approval workflow
        workflow_input = APInvoiceApprovalWorkflowInput(invoice_id=invoice_id)
        await workflow.start_child_workflow(
            InvoiceApprovalWorkflow.execute,
            args=[workflow_input],
            id=f"invoice-approval-{invoice_id}",
            parent_close_policy=workflow.ParentClosePolicy.ABANDON,
        )

    def _build_email_update_params(
        self, message_id: str, gcs_path: str, status: str
    ) -> RelationalUpdateParams:
        """Build update parameters for email record"""
        return RelationalUpdateParams(
            table=ZAMPAPAGENTEMAILS,
            data={"storage_path": gcs_path, "status": status},
            where={"message_id": message_id},
        )

    async def _generate_uuid(self) -> str:
        result = await workflow.execute_activity(
            execute_code,
            args=[
                CodeExecutorConfig(timeout_seconds=5),
                ExecuteCodeParams(function=get_fqn(generate_random_uuid)),
            ],
            start_to_close_timeout=datetime.timedelta(seconds=10),
        )
        return result.result

    async def _get_current_time(self) -> datetime.datetime:
        result = await workflow.execute_activity(
            execute_code,
            args=[
                CodeExecutorConfig(timeout_seconds=5),
                ExecuteCodeParams(function=get_fqn(get_current_time)),
            ],
            start_to_close_timeout=datetime.timedelta(seconds=10),
        )
        return datetime.datetime.fromisoformat(result.result)


def construct_email_records(
    unprocessed_emails: List[GmailMessage],
) -> Tuple[List[ZampApAgentEmailSchema], List[str]]:
    email_records: List[ZampApAgentEmailSchema] = []
    unprocessed_emails_ids: List[str] = []

    for email in unprocessed_emails:
        email_uuid = generate_random_uuid()
        received_at = email.date.astimezone(UTC).replace(tzinfo=None)
        current_time = get_current_time()

        email_records.append(
            ZampApAgentEmailSchema(
                id=UUID(email_uuid),
                message_id=email.id,
                subject=email.subject,
                **{"from": email.sender},
                received_at=received_at,
                storage_path="",
                status=STATUS_UNPROCESSED,
                created_at=current_time,
                updated_at=current_time,
            )
        )

        unprocessed_emails_ids.append(email_uuid)

    return email_records, unprocessed_emails_ids
