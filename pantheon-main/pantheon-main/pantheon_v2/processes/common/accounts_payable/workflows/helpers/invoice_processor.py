from temporalio import workflow
import datetime
from typing import List, Dict
import json
from dateutil import parser

from pantheon_v2.processes.common.accounts_payable.models.invoice_approval_models import (
    ProcessedFileInfo,
)
from pantheon_v2.tools.core.internal_data_repository.models import (
    RelationalUpdateParams,
)
from pantheon_v2.tools.core.internal_data_repository.activities import (
    update_internal_relational_data,
)
from pantheon_v2.utils.dto.util_dto import DateTimeEncoder
from pantheon_v2.processes.common.accounts_payable.constants.invoice_approval_constants import (
    INVOICE_TABLE,
)


def filter_invoice_files(
    processed_files: List[ProcessedFileInfo],
) -> List[ProcessedFileInfo]:
    """Filter files to only include valid invoices"""
    return [
        file
        for file in processed_files
        if file.extracted_data and file.extracted_data.is_invoice
    ]


def prepare_metadata(
    processed_file: ProcessedFileInfo,
    approvers_data: Dict,
    all_files: List[ProcessedFileInfo],
) -> Dict:
    """Prepare metadata for invoice update"""
    return {
        "ocr_details": processed_file.extracted_data.model_dump(),
        "approval_hierarchy": approvers_data,
        "file_details": [file.model_dump() for file in all_files],
    }


async def update_invoice(
    invoice_id: str, processed_file: ProcessedFileInfo, metadata: Dict
):
    """Update invoice with processed data"""
    metadata_json = json.dumps(metadata, cls=DateTimeEncoder)
    extracted_data = processed_file.extracted_data

    values = {
        "metadata": metadata_json,
        "amount": round(float(extracted_data.total_amount), 2),
        "currency": extracted_data.currency,
        "description": extracted_data.description,
        "invoicebucketpath": processed_file.full_path,
        "invoiceid": extracted_data.invoice_number,
    }

    # Add dates if available
    if extracted_data.issue_date:
        values["invoicedate"] = parser.parse(extracted_data.issue_date).date()
    if extracted_data.due_date:
        values["duedate"] = parser.parse(extracted_data.due_date).date()

    update_params = RelationalUpdateParams(
        table=INVOICE_TABLE,
        data=values,
        where={"id": invoice_id},
    )

    await workflow.execute_activity(
        update_internal_relational_data,
        args=[update_params],
        start_to_close_timeout=datetime.timedelta(seconds=30),
    )
