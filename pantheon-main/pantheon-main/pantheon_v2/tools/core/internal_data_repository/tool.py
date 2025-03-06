from typing import TypeVar
from pydantic import BaseModel
from pantheon_v2.tools.core.internal_data_repository.models import (
    RelationalQueryParams,
    RelationalInsertParams,
    RelationalUpdateParams,
    BlobStorageQueryParams,
    RelationalQueryResult,
    RelationalExecuteResult,
    BlobStorageResult,
    BlobStorageUploadParams,
    BlobStorageUploadResult,
    BlobStorageFolderQueryParams,
    BlobStorageFolderResult,
    BlobStorageFile,
)

from pantheon_v2.tools.core.base import BaseTool

from pantheon_v2.tools.external.postgres.tool import PostgresTool
from pantheon_v2.tools.external.postgres.models import (
    QueryParams,
    BatchInsertParams,
    UpdateParams,
    TableInsert,
)

from pantheon_v2.tools.external.gcs.models import (
    UploadToGCSInput,
    DownloadFromGCSInput,
)

from pantheon_v2.tools.external.gcs.tool import GCSTool

from pantheon_v2.tools.core.internal_data_repository.constants import (
    INTERNAL_POSTGRES_CONFIG,
    INTERNAL_GCS_CONFIG,
)

T = TypeVar("T", bound=BaseModel)


class InternalDataRepositoryTool(BaseTool):
    async def initialize(self) -> None:
        self.postgres_tool = PostgresTool(INTERNAL_POSTGRES_CONFIG.model_dump())
        await self.postgres_tool.initialize()
        self.gcs_tool = GCSTool(INTERNAL_GCS_CONFIG.model_dump())
        await self.gcs_tool.initialize()

    async def query_relational_data(
        self, query_params: RelationalQueryParams
    ) -> RelationalQueryResult:
        postgres_result = await self.postgres_tool.query(
            QueryParams(**query_params.model_dump())
        )
        return RelationalQueryResult(
            data=[query_params.output_model(**row) for row in postgres_result.rows],
            row_count=postgres_result.row_count,
        )

    async def insert_relational_data(
        self, insert_params: RelationalInsertParams
    ) -> RelationalExecuteResult:
        insertParams = BatchInsertParams(operations=[])
        for operation in insert_params.data:
            insertParams.operations.append(
                TableInsert(
                    table=insert_params.table,
                    values=operation.model_dump(by_alias=True),
                )
            )

        postgres_result = await self.postgres_tool.insert(insertParams)
        return RelationalExecuteResult(
            success=postgres_result.success,
            affected_rows=postgres_result.affected_rows,
        )

    async def update_relational_data(
        self, update_params: RelationalUpdateParams
    ) -> RelationalExecuteResult:
        update_params = UpdateParams(
            table=update_params.table,
            values=update_params.data,
            where=update_params.where,
        )

        postgres_result = await self.postgres_tool.update(update_params)
        return RelationalExecuteResult(
            success=postgres_result.success,
            affected_rows=postgres_result.affected_rows,
        )

    async def query_blob_storage(
        self, query_params: BlobStorageQueryParams
    ) -> BlobStorageResult:
        result = await self.gcs_tool.download_from_gcs(
            DownloadFromGCSInput(
                bucket_name=query_params.bucket_name,
                file_name=query_params.file_name,
            )
        )

        return BlobStorageResult(
            content=result.content.getvalue(),
        )

    async def upload_to_blob_storage(
        self, upload_params: BlobStorageUploadParams
    ) -> BlobStorageUploadResult:
        result = await self.gcs_tool.upload_to_gcs(
            UploadToGCSInput(
                bucket_name=upload_params.bucket_name,
                file_name=upload_params.file_name,
                blob=upload_params.blob,
            )
        )

        return BlobStorageUploadResult(
            metadata=result.metadata,
            gcs_url=result.gcs_url,
            https_url=result.https_url,
        )

    async def query_blob_storage_folder(
        self, query_params: BlobStorageFolderQueryParams
    ) -> BlobStorageFolderResult:
        result = await self.gcs_tool.download_folder_from_gcs(
            query_params.bucket_name, query_params.folder_path
        )

        return BlobStorageFolderResult(
            files=[
                BlobStorageFile.from_gcs_file_metadata(file) for file in result.files
            ]
        )
