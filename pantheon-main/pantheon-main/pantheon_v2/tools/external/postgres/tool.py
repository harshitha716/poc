import structlog
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from pantheon_v2.tools.core.base import BaseTool
from pantheon_v2.tools.core.tool_registry import ToolRegistry
from pantheon_v2.tools.external.postgres.config import PostgresConfig
from pantheon_v2.tools.external.postgres.models import (
    QueryParams,
    UpdateParams,
    QueryResult,
    ExecuteResult,
    BatchInsertParams,
)

logger = structlog.get_logger(__name__)


@ToolRegistry.register_tool(
    "PostgreSQL database tool for executing queries and managing data"
)
class PostgresTool(BaseTool):
    def __init__(self, config: dict):
        self.engine = None
        self.async_session = None
        self.config = config

    async def initialize(self) -> None:
        """Initialize the Postgres connection asynchronously"""
        try:
            config = PostgresConfig(**self.config)
            self.engine = await self._create_engine(config)
            self.async_session = sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )
            logger.info("Postgres tool initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Postgres tool", error=str(e))
            raise

    async def _create_engine(self, config: PostgresConfig):
        """Create async SQLAlchemy engine"""
        try:
            connection_string = (
                f"postgresql+asyncpg://{config.username}:{config.password}@"
                f"{config.host}:{config.port}/{config.database}"
            )
            engine = create_async_engine(
                connection_string,
                pool_size=config.pool_size,
                max_overflow=config.max_overflow,
            )
            return engine

        except Exception as e:
            logger.error("Failed to create database engine", error=str(e))
            raise

    @ToolRegistry.register_tool_action("Execute a SELECT query on the database")
    async def query(self, params: QueryParams) -> QueryResult:
        """Execute a SELECT query and return the results"""
        try:
            async with self.async_session() as session:
                result = await session.execute(
                    text(params.query), params.parameters or {}
                )

                if result.returns_rows:
                    columns = result.keys()
                    rows = [dict(zip(columns, row)) for row in result.fetchall()]
                    return QueryResult(columns=columns, rows=rows, row_count=len(rows))
                return QueryResult(columns=[], rows=[], row_count=0)
        except Exception as e:
            logger.error("Query execution failed", error=str(e))
            raise

    @ToolRegistry.register_tool_action("Insert data into the database")
    async def insert(self, params: BatchInsertParams) -> ExecuteResult:
        """Insert multiple records across different tables within a single transaction"""
        try:
            async with self.async_session() as session:
                transaction = await session.begin()
                try:
                    total_rows = 0

                    for operation in params.operations:
                        # Quote column names to handle reserved keywords
                        quoted_columns = [f'"{col}"' for col in operation.values.keys()]
                        columns_str = ", ".join(quoted_columns)
                        placeholders = ", ".join(
                            f":{col}" for col in operation.values.keys()
                        )

                        query = f"INSERT INTO {operation.table} ({columns_str}) VALUES ({placeholders})"

                        result = await session.execute(text(query), operation.values)
                        total_rows += result.rowcount

                    await session.commit()
                    return ExecuteResult(success=True, affected_rows=total_rows)
                except:
                    await transaction.rollback()
                    raise
        except Exception as e:
            logger.error("Insert operation failed", error=str(e))
            raise

    @ToolRegistry.register_tool_action("Update data in the database")
    async def update(self, params: UpdateParams) -> ExecuteResult:
        """Update records in the specified table"""
        try:
            set_clause = ", ".join(f"{k} = :{k}" for k in params.values.keys())
            where_clause = " AND ".join(
                f"{k} = :{k}_where" for k in params.where.keys()
            )

            query = f"UPDATE {params.table} SET {set_clause} WHERE {where_clause}"

            # Prepare parameters
            parameters = {**params.values}
            parameters.update({f"{k}_where": v for k, v in params.where.items()})

            async with self.async_session() as session:
                transaction = await session.begin()
                try:
                    result = await session.execute(text(query), parameters)
                    await session.commit()
                    return ExecuteResult(success=True, affected_rows=result.rowcount)
                except:
                    await transaction.rollback()
                    raise
        except Exception as e:
            logger.error("Update operation failed", error=str(e))
            raise
