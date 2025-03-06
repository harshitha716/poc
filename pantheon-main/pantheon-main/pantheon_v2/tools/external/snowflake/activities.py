from pantheon_v2.tools.external.snowflake.tool import SnowflakeTool
from pantheon_v2.tools.external.snowflake.config import SnowflakeConfig
from pantheon_v2.tools.external.snowflake.models import (
    QueryParams,
    InsertParams,
    UpdateParams,
    DeleteParams,
)

from pantheon_v2.tools.external.snowflake.models import (
    QueryResult,
    ExecuteResult,
)

from pantheon_v2.tools.core.activity_registry import ActivityRegistry


@ActivityRegistry.register_activity("Execute a SELECT query on the Snowflake database")
async def query_snowflake_data(
    config: SnowflakeConfig, params: QueryParams
) -> QueryResult:
    tool = SnowflakeTool(config)
    await tool.initialize()
    return await tool.query(params)


@ActivityRegistry.register_activity("Insert data into the Snowflake database")
async def insert_snowflake_data(
    config: SnowflakeConfig, params: InsertParams
) -> ExecuteResult:
    tool = SnowflakeTool(config)
    await tool.initialize()
    return await tool.insert(params)


@ActivityRegistry.register_activity("Update data in the Snowflake database")
async def update_snowflake_data(
    config: SnowflakeConfig, params: UpdateParams
) -> ExecuteResult:
    tool = SnowflakeTool(config)
    await tool.initialize()
    return await tool.update(params)


@ActivityRegistry.register_activity("Delete data from the Snowflake database")
async def delete_snowflake_data(
    config: SnowflakeConfig, params: DeleteParams
) -> ExecuteResult:
    tool = SnowflakeTool(config)
    await tool.initialize()
    return await tool.delete(params)
