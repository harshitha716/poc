from pantheon_v2.utils.type_utils import get_fqn, get_reference_from_fqn

from pydantic import BaseModel
from io import BytesIO
from typing import Any, Type, TypeVar, Dict
from datetime import datetime

from pantheon_v2.tools.external.gcs.models import GCSFileMetadata

T = TypeVar("T", bound=BaseModel)

"""
QueryParams is a model that contains the query and the parameters for the query.
"""


class RelationalQueryParams(BaseModel):
    query: str
    parameters: dict
    output_model: Type[BaseModel]


class RelationalQueryResult[T: BaseModel](BaseModel):
    data: list[T]
    row_count: int
    __data_type: str

    @classmethod
    def model_validate(cls, obj: dict) -> "RelationalQueryResult":
        if "__data_type" in obj:
            data_type = get_reference_from_fqn(obj.pop("__data_type"))
            obj["data"] = [data_type.model_validate(item) for item in obj["data"]]
        return super().model_validate(obj)

    def model_dump(self, *args, **kwargs):
        d = super().model_dump(*args, **kwargs)
        d["__data_type"] = get_fqn(self.data[0].__class__)
        return d


"""
INSERT Models
"""


class RelationalInsertParams[T: BaseModel](BaseModel):
    table: str
    data: list[T]


"""
UPDATE Models
"""


class RelationalUpdateParams[T: BaseModel](BaseModel):
    table: str
    data: dict[str, Any]
    where: dict[str, Any]


"""
Result Models
"""


class RelationalExecuteResult(BaseModel):
    success: bool
    affected_rows: int


"""
Blob Storage Models
"""


class BlobStorageQueryParams(BaseModel):
    bucket_name: str
    file_name: str


class BlobStorageResult(BaseModel):
    content: bytes

    class Config:
        arbitrary_types_allowed = True


class BlobStorageFile(BaseModel):
    name: str
    full_path: str
    relative_path: str
    size: int
    content_type: str
    created: datetime
    updated: datetime
    content: bytes

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_gcs_file_metadata(cls, metadata: GCSFileMetadata) -> "BlobStorageFile":
        return cls(
            name=metadata.name,
            full_path=metadata.full_path,
            relative_path=metadata.relative_path,
            size=metadata.size,
            content_type=metadata.content_type,
            created=metadata.created,
            updated=metadata.updated,
            content=metadata.content.getvalue(),
        )


class BlobStorageFolderQueryParams(BaseModel):
    bucket_name: str
    folder_path: str


class BlobStorageFolderResult(BaseModel):
    files: list[BlobStorageFile]

    class Config:
        arbitrary_types_allowed = True


class BlobStorageUploadParams(BaseModel):
    bucket_name: str
    file_name: str
    blob: BytesIO

    class Config:
        arbitrary_types_allowed = True


class BlobStorageUploadResult(BaseModel):
    metadata: dict
    gcs_url: str
    https_url: str


class BlobStorageQueryResult(BaseModel):
    content: bytes
    metadata: Dict[str, Any] = {}
