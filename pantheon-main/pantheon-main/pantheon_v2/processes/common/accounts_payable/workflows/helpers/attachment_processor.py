from temporalio import workflow
import base64
from typing import List
import datetime

from pantheon_v2.processes.common.accounts_payable.models.invoice_approval_models import (
    ProcessedFileInfo,
    InvoiceData,
    FetchInvoiceQueryResult,
)
from pantheon_v2.tools.core.internal_data_repository.models import (
    RelationalQueryParams,
    BlobStorageFolderQueryParams,
)
from pantheon_v2.tools.core.internal_data_repository.activities import (
    query_internal_relational_data,
    query_internal_blob_storage_folder,
)
from pantheon_v2.tools.common.ocr.models import (
    OCRExtractInput,
    ExtractionType,
    OCRExtractOutput,
)
from pantheon_v2.tools.core.internal_data_repository.models import (
    BlobStorageFolderResult,
    BlobStorageFile,
)
from pantheon_v2.tools.common.ocr.activities import extract_ocr_data
from pantheon_v2.processes.common.accounts_payable.constants.invoice_approval_constants import (
    INVOICE_QUERY,
)


async def fetch_invoice_data(invoice_id: str) -> FetchInvoiceQueryResult:
    query_params = RelationalQueryParams(
        query=INVOICE_QUERY,
        parameters={"invoice_id": invoice_id},
        output_model=FetchInvoiceQueryResult,
    )

    result = await workflow.execute_activity(
        query_internal_relational_data,
        args=[query_params],
        start_to_close_timeout=datetime.timedelta(seconds=30),
    )

    if not result.data:
        raise ValueError(f"No data found for invoice_id: {invoice_id}")

    return result.data[0]


async def process_attachments(
    invoice_data: FetchInvoiceQueryResult,
) -> List[ProcessedFileInfo]:
    gcs_path = invoice_data.gcspath.replace("gs://", "")
    bucket_name, folder_path = gcs_path.split("/", 1)

    query_params = BlobStorageFolderQueryParams(
        bucket_name=bucket_name, folder_path=folder_path
    )
    files: BlobStorageFolderResult = await workflow.execute_activity(
        query_internal_blob_storage_folder,
        args=[query_params],
        start_to_close_timeout=datetime.timedelta(minutes=10),
    )

    if not files.files:
        raise ValueError(f"No files found in GCS path: {gcs_path}")

    processed_files = []
    for file in files.files:
        processed_file = await process_single_file(file)
        processed_files.append(processed_file)

    return processed_files


async def process_single_file(file: BlobStorageFile) -> ProcessedFileInfo:
    encoded_file = base64.b64encode(file.content).decode("utf-8")

    ocr_response: OCRExtractOutput[InvoiceData] = await workflow.execute_activity(
        extract_ocr_data,
        args=[
            OCRExtractInput(
                file_content=[encoded_file],
                extract_dto=InvoiceData,
                extraction_type=ExtractionType.INVOICE,
            )
        ],
        result_type=OCRExtractOutput[InvoiceData],
        start_to_close_timeout=datetime.timedelta(minutes=20),
    )

    return ProcessedFileInfo(
        name=file.name,
        full_path=file.full_path,
        relative_path=file.relative_path,
        size=file.size,
        content_type=file.content_type,
        created=file.created,
        updated=file.updated,
        extracted_data=ocr_response.extracted_data,
    )
