from pantheon_v2.tools.core.activity_registry import ActivityRegistry
from pantheon_v2.tools.external.s3.config import S3Config
from pantheon_v2.tools.external.s3.models import (
    DownloadFromS3Input,
    DownloadFromS3Output,
    UploadToS3Input,
    UploadToS3Output,
    DownloadFolderFromS3Input,
    DownloadFolderFromS3Output,
)
from pantheon_v2.tools.external.s3.tool import S3Tool
from pantheon_v2.settings.settings import Settings


def get_internal_s3_config() -> (
    S3Config
):  # TODO: remove and integrate with connectivity service to share credentials. removed config for now
    """Get the internal S3 configuration with credentials from settings"""
    return S3Config(
        aws_access_key=Settings.AWS_ACCESS_KEY_ID,
        aws_secret_key=Settings.AWS_SECRET_ACCESS_KEY,
        region_name=Settings.AWS_REGION,
    )


@ActivityRegistry.register_activity("Download a file from Amazon S3")
async def download_from_s3(input: DownloadFromS3Input) -> DownloadFromS3Output:
    config = get_internal_s3_config()
    tool = S3Tool(config.model_dump())
    await tool.initialize()
    output = await tool.download_from_s3(input)
    return output


@ActivityRegistry.register_activity("Upload a file to Amazon S3")
async def upload_to_s3(input: UploadToS3Input) -> UploadToS3Output:
    config = get_internal_s3_config()
    tool = S3Tool(config.model_dump())
    await tool.initialize()
    return await tool.upload_to_s3(input)


@ActivityRegistry.register_activity("Download a folder from Amazon S3")
async def download_folder_from_s3(
    input: DownloadFolderFromS3Input,
) -> DownloadFolderFromS3Output:
    config = get_internal_s3_config()
    tool = S3Tool(config.model_dump())
    await tool.initialize()
    return await tool.download_folder_from_s3(input.bucket_name, input.folder_path)
