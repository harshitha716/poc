from pantheon_v2.tools.core.activity_registry import ActivityRegistry

from pantheon_v2.tools.core.internal_data_repository.models import (
    RelationalQueryParams,
    RelationalQueryResult,
    RelationalInsertParams,
    RelationalUpdateParams,
    RelationalExecuteResult,
    BlobStorageQueryParams,
    BlobStorageResult,
    BlobStorageFolderQueryParams,
    BlobStorageFolderResult,
    BlobStorageUploadParams,
    BlobStorageUploadResult,
)

from pantheon_v2.tools.core.internal_data_repository.tool import (
    InternalDataRepositoryTool,
)


@ActivityRegistry.register_activity("Query relational data from internal zamp systems")
async def query_internal_relational_data(
    query_params: RelationalQueryParams,
) -> RelationalQueryResult:
    tool = InternalDataRepositoryTool()
    await tool.initialize()
    return await tool.query_relational_data(query_params)


@ActivityRegistry.register_activity("Insert data into internal zamp systems")
async def insert_internal_relational_data(
    insert_params: RelationalInsertParams,
) -> RelationalExecuteResult:
    tool = InternalDataRepositoryTool()
    await tool.initialize()
    return await tool.insert_relational_data(insert_params)


@ActivityRegistry.register_activity("Update data in internal zamp systems")
async def update_internal_relational_data(
    update_params: RelationalUpdateParams,
) -> RelationalExecuteResult:
    tool = InternalDataRepositoryTool()
    await tool.initialize()
    return await tool.update_relational_data(update_params)


@ActivityRegistry.register_activity(
    "Query blob storage from internal zamp storage blob bucket"
)
async def query_internal_blob_storage(
    query_params: BlobStorageQueryParams,
) -> BlobStorageResult:
    tool = InternalDataRepositoryTool()
    await tool.initialize()
    return await tool.query_blob_storage(query_params)


@ActivityRegistry.register_activity(
    "Query blob storage folder from internal zamp storage blob bucket"
)
async def query_internal_blob_storage_folder(
    query_params: BlobStorageFolderQueryParams,
) -> BlobStorageFolderResult:
    tool = InternalDataRepositoryTool()
    await tool.initialize()
    return await tool.query_blob_storage_folder(query_params)


@ActivityRegistry.register_activity("Upload file to internal zamp storage blob bucket")
async def upload_internal_blob_storage(
    upload_params: BlobStorageUploadParams,
) -> BlobStorageUploadResult:
    tool = InternalDataRepositoryTool()
    await tool.initialize()
    return await tool.upload_to_blob_storage(upload_params)
