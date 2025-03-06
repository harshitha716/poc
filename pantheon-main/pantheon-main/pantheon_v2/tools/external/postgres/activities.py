from pantheon_v2.tools.external.postgres.tool import PostgresTool
from pantheon_v2.tools.external.postgres.config import PostgresConfig
from pantheon_v2.tools.external.postgres.models import (
    QueryParams,
    BatchInsertParams,
    UpdateParams,
    QueryResult,
    ExecuteResult,
)
from pantheon_v2.tools.core.activity_registry import ActivityRegistry


@ActivityRegistry.register_activity("Execute a SELECT query on the PostgreSQL database")
async def query(config: PostgresConfig, params: QueryParams) -> QueryResult:
    tool = PostgresTool(config)
    await tool.initialize()
    return await tool.query(params)


@ActivityRegistry.register_activity("Insert data into the PostgreSQL database")
async def insert(config: PostgresConfig, params: BatchInsertParams) -> ExecuteResult:
    tool = PostgresTool(config)
    await tool.initialize()
    return await tool.insert(params)


@ActivityRegistry.register_activity("Update data in the PostgreSQL database")
async def update(config: PostgresConfig, params: UpdateParams) -> ExecuteResult:
    tool = PostgresTool(config)
    await tool.initialize()
    return await tool.update(params)
