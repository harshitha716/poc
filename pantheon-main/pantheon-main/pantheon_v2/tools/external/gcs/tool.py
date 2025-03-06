import structlog
import os
from google.cloud import storage
from io import BytesIO
import mimetypes

from pantheon_v2.tools.external.gcs.models import (
    DownloadFromGCSInput,
    DownloadFromGCSOutput,
    UploadToGCSInput,
    UploadToGCSOutput,
    DownloadFolderFromGCSOutput,
    GCSFileMetadata,
)
from pantheon_v2.tools.core.base import BaseTool
from pantheon_v2.tools.core.tool_registry import ToolRegistry
from pantheon_v2.tools.external.gcs.config import GCSConfig
from pantheon_v2.tools.external.gcs.constants import GCS_HTTPS_BASE_URL

logger = structlog.get_logger(__name__)


@ToolRegistry.register_tool(description="Google Cloud Storage tool for file operations")
class GCSTool(BaseTool):
    def __init__(self, config: dict):
        self.storage_client = None
        self.config = config

    async def initialize(self) -> None:
        """Initialize the GCS client asynchronously"""
        try:
            config = GCSConfig(**self.config)

            self.storage_client = storage.Client(config.project_id)
            logger.info("GCS tool initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize GCS tool", error=str(e))
            raise

    @ToolRegistry.register_tool_action(
        description="Download a file from Google Cloud Storage"
    )
    async def download_from_gcs(
        self, params: DownloadFromGCSInput
    ) -> DownloadFromGCSOutput:
        bucket = self.storage_client.get_bucket(params.bucket_name)
        blob = bucket.blob(params.file_name)

        # Create an in-memory file-like object
        bytes_buffer = BytesIO()
        blob.download_to_file(bytes_buffer)
        bytes_buffer.seek(0)  # Move to the beginning of the file-like object

        return DownloadFromGCSOutput(content=bytes_buffer)

    @ToolRegistry.register_tool_action(
        description="Upload a file to Google Cloud Storage"
    )
    async def upload_to_gcs(self, params: UploadToGCSInput) -> UploadToGCSOutput:
        bucket = self.storage_client.get_bucket(params.bucket_name)
        gcs_blob = bucket.blob(params.file_name)

        if params.preview_enabled:
            gcs_blob.content_disposition = "inline"

        # Detect content type from the file name
        content_type, _ = mimetypes.guess_type(params.file_name)
        if content_type is None:
            content_type = (
                "application/octet-stream"  # default content type if unable to detect
            )

        # Use the existing BytesIO object directly
        params.blob.seek(0)  # Ensure we're at the start of the BytesIO object
        gcs_blob.upload_from_file(params.blob, content_type=content_type)

        metadata = {
            "bucket": params.bucket_name,
            "name": params.file_name,
            "size": gcs_blob.size,
            "content_type": gcs_blob.content_type,
            "etag": gcs_blob.etag,
            "generation": gcs_blob.generation,
            "metageneration": gcs_blob.metageneration,
            "content_disposition": gcs_blob.content_disposition,
        }

        gcs_url = f"gs://{params.bucket_name}/{params.file_name}"
        https_url = f"{GCS_HTTPS_BASE_URL}/{params.bucket_name}/{params.file_name}"

        return UploadToGCSOutput(
            metadata=metadata, gcs_url=gcs_url, https_url=https_url
        )

    @ToolRegistry.register_tool_action(
        description="Download a folder from Google Cloud Storage"
    )
    async def download_folder_from_gcs(
        self,
        bucket_name: str,
        folder_path: str,
    ) -> DownloadFolderFromGCSOutput:
        """Downloads all contents of a GCS folder and returns array of BytesIO objects with metadata"""
        bucket = self.storage_client.get_bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=folder_path)

        downloaded_files = []
        for blob in blobs:
            if blob.name.endswith("/"):  # Skip folder markers
                continue

            # Create BytesIO object for the file
            bytes_buffer = BytesIO()
            blob.download_to_file(bytes_buffer)
            bytes_buffer.seek(0)  # Move to the beginning of the file-like object

            # Extract relative path by removing the folder_path prefix
            relative_path = blob.name.replace(folder_path, "").lstrip("/")
            full_path = f"gs://{bucket_name}/{blob.name}"

            # Create metadata object
            metadata = GCSFileMetadata(
                name=os.path.basename(blob.name),
                full_path=full_path,
                relative_path=relative_path,
                size=blob.size,
                content_type=blob.content_type,
                created=blob.time_created,
                updated=blob.updated,
                content=bytes_buffer,
            )

            downloaded_files.append(metadata)

        return DownloadFolderFromGCSOutput(
            message=f"Downloaded {len(downloaded_files)} files", files=downloaded_files
        )
