from io import BytesIO
from typing import Dict
from datetime import datetime
from pydantic import BaseModel, Field
from pantheon_v2.core.custom_data_types.pydantic import SerializableBytesIO


class DownloadFromGCSInput(BaseModel):
    bucket_name: str = Field(..., description="Name of the GCS bucket to download from")
    file_name: str = Field(..., description="Name of the file to download")


class DownloadFromGCSOutput(BaseModel):
    content: SerializableBytesIO = Field(
        ..., description="File content as BytesIO object"
    )

    class Config:
        arbitrary_types_allowed = True


class UploadToGCSInput(BaseModel):
    bucket_name: str = Field(..., description="Name of the GCS bucket to upload to")
    file_name: str = Field(..., description="Name to give the uploaded file")
    blob: BytesIO = Field(..., description="File content as BytesIO object")
    preview_enabled: bool = Field(
        default=False,
        description="If True, sets response_disposition to 'inline' for browser preview",
    )

    class Config:
        arbitrary_types_allowed = True


class UploadToGCSOutput(BaseModel):
    metadata: Dict = Field(..., description="Metadata of the uploaded file")
    gcs_url: str = Field(..., description="GCS URL of the uploaded file (gs://...)")
    https_url: str = Field(
        ...,
        description="HTTPS URL of the uploaded file (https://storage.googleapis.com/...)",
    )


class GCSFileMetadata(BaseModel):
    name: str = Field(..., description="Name of the file")
    full_path: str = Field(..., description="Full path of the file in GCS")
    relative_path: str = Field(
        ..., description="Path relative to the folder being downloaded"
    )
    size: int = Field(..., description="Size of the file in bytes")
    content_type: str = Field(..., description="Content type of the file")
    created: datetime = Field(..., description="Creation timestamp")
    updated: datetime = Field(..., description="Last update timestamp")
    content: BytesIO = Field(..., description="File content as BytesIO object")

    class Config:
        arbitrary_types_allowed = True


class DownloadFolderFromGCSOutput(BaseModel):
    message: str = Field(..., description="Status message")
    files: list[GCSFileMetadata] = Field(
        ..., description="List of downloaded files with metadata"
    )

    class Config:
        arbitrary_types_allowed = True


class DownloadFolderFromGCSInput(BaseModel):
    bucket_name: str = Field(..., description="Name of the GCS bucket to download from")
    folder_path: str = Field(..., description="Path to the folder to download")
