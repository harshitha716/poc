from pantheon_v2.tools.external.gcs.tool import GCSTool
from pantheon_v2.tools.external.gcs.config import GCSConfig
from pantheon_v2.tools.external.gcs.models import (
    DownloadFromGCSInput,
    DownloadFromGCSOutput,
    UploadToGCSInput,
    UploadToGCSOutput,
    DownloadFolderFromGCSInput,
    DownloadFolderFromGCSOutput,
)

from pantheon_v2.tools.core.activity_registry import ActivityRegistry


@ActivityRegistry.register_activity("Download a file from Google Cloud Storage")
async def download_from_gcs(
    config: GCSConfig, input: DownloadFromGCSInput
) -> DownloadFromGCSOutput:
    tool = GCSTool(config)
    await tool.initialize()
    return await tool.download_from_gcs(input)


@ActivityRegistry.register_activity("Upload a file to Google Cloud Storage")
async def upload_to_gcs(
    config: GCSConfig, input: UploadToGCSInput
) -> UploadToGCSOutput:
    tool = GCSTool(config)
    await tool.initialize()
    return await tool.upload_to_gcs(input)


@ActivityRegistry.register_activity("Download a folder from Google Cloud Storage")
async def download_folder_from_gcs(
    config: GCSConfig, input: DownloadFolderFromGCSInput
) -> DownloadFolderFromGCSOutput:
    tool = GCSTool(config)
    await tool.initialize()
    return await tool.download_folder_from_gcs(input.bucket_name, input.folder_path)
