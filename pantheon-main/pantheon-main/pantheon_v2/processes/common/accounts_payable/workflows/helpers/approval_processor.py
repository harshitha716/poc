from temporalio import workflow
import datetime
from typing import Optional
import json

from pantheon_v2.processes.common.accounts_payable.models.invoice_approval_models import (
    ApprovalResponse,
    FetchInvoiceMetadataQueryResult,
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
    METADATA_QUERY,
    INVOICE_TABLE,
    APPROVAL_HIERARCHY_KEY,
)

import structlog

logger = structlog.get_logger(__name__)


async def fetch_invoice_metadata(invoice_id: str) -> dict:
    query_params = RelationalQueryParams(
        query=METADATA_QUERY,
        parameters={"invoice_id": invoice_id},
        output_model=FetchInvoiceMetadataQueryResult,
    )

    result = await workflow.execute_activity(
        query_internal_relational_data,
        args=[query_params],
        start_to_close_timeout=datetime.timedelta(seconds=30),
    )

    if not result.data:
        raise ValueError(f"No invoice found with id: {invoice_id}")

    metadata = result.data[0].metadata
    if not metadata:
        raise ValueError(f"No metadata found for invoice: {invoice_id}")

    approval_hierarchy = metadata.get(APPROVAL_HIERARCHY_KEY)
    if not approval_hierarchy:
        raise ValueError(
            f"No approval hierarchy found in metadata for invoice: {invoice_id}"
        )

    return metadata


def get_next_approver(metadata: dict, is_initial_fetch: bool = False) -> Optional[str]:
    if APPROVAL_HIERARCHY_KEY not in metadata:
        return None

    approval_hierarchy = metadata[APPROVAL_HIERARCHY_KEY]
    for approver in approval_hierarchy:
        if approver.get("status", "").lower() == "disapprove":
            raise ValueError(f"Invoice has been disapproved by {approver.get('email')}")

        if not approver.get("status"):
            return approver.get("email")

    if is_initial_fetch:
        raise ValueError("No pending approvers found in the approval hierarchy")
    else:
        return None


def update_approver_status(
    metadata: dict, email: str, approval_response: ApprovalResponse
) -> None:
    approval_hierarchy = metadata.get(APPROVAL_HIERARCHY_KEY)
    approver_found = False

    for approver in approval_hierarchy:
        if approver.get("email") == email:
            approver["status"] = approval_response.status
            approver["message"] = approval_response.message
            approver_found = True
            break

    if not approver_found:
        raise ValueError(f"Approver {email} not found in approval hierarchy")


async def update_metadata_in_db(invoice_id: str, metadata: dict):
    update_params = RelationalUpdateParams(
        table=INVOICE_TABLE,
        data={"metadata": json.dumps(metadata)},
        where={"id": invoice_id},
    )

    await workflow.execute_activity(
        update_internal_relational_data,
        args=[update_params],
        start_to_close_timeout=datetime.timedelta(seconds=30),
    )
