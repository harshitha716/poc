import structlog
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pantheon_v2.tools.external.snowflake.config import SnowflakeConfig
from pantheon_v2.tools.core.base import BaseTool
from pantheon_v2.tools.core.tool_registry import ToolRegistry
from pantheon_v2.tools.external.snowflake.models import (
    QueryParams,
    InsertParams,
    UpdateParams,
    QueryResult,
    ExecuteResult,
    DeleteParams,
)

from typing import Type, TypeVar
from pydantic import BaseModel  # Import Pydantic BaseModel

logger = structlog.get_logger(__name__)

T = TypeVar("T", bound=BaseModel)  # Bind T to Pydantic BaseModel


@ToolRegistry.register_tool(
    description="Snowflake database tool for executing queries and managing data"
)
class SnowflakeTool(BaseTool):
    def __init__(self, config: dict):
        self.engine = None
        self.session = None
        self.config = config

    async def initialize(self) -> None:
        """Initialize the Snowflake connection using SQLAlchemy"""
        try:
            config = SnowflakeConfig(**self.config)
            connection_string = (
                f"snowflake://{config.user}:{config.password}@{config.account}/"
                f"{config.database}/{config.schema}?warehouse={config.warehouse}"
            )
            self.engine = create_engine(connection_string)
            self.session = sessionmaker(bind=self.engine)
            logger.info("Snowflake tool initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Snowflake tool", error=str(e))
            raise

    @ToolRegistry.register_tool_action(
        description="Execute a SELECT query on the database"
    )
    async def query(self, params: QueryParams[T]) -> QueryResult:
        """Execute a SELECT query and return the results"""
        try:
            with self.session() as session:
                query = session.query(params.model).filter_by(**params.parameters)
                rows = query.all()
                columns = params.model.__table__.columns.keys()
                return QueryResult(
                    columns=columns,
                    rows=[row.to_dict() for row in rows],
                    row_count=len(rows),
                )
        except Exception as e:
            logger.error("Query execution failed", error=str(e))
            raise

    @ToolRegistry.register_tool_action(description="Insert data into the database")
    async def insert(self, params: InsertParams[T]) -> ExecuteResult:
        """Insert records into the specified table"""
        try:
            with self.session() as session:
                for values in params.values:
                    new_record = params.model(**values)
                    session.add(new_record)
                session.commit()
                return ExecuteResult(success=True, affected_rows=len(params.values))
        except Exception as e:
            logger.error("Insert operation failed", error=str(e))
            raise

    @ToolRegistry.register_tool_action(description="Update data in the database")
    async def update(self, model: Type[T], params: UpdateParams) -> ExecuteResult:
        """Update records in the specified table"""
        try:
            with self.session() as session:
                query = session.query(model).filter_by(**params.where)
                affected_rows = query.update(params.values, synchronize_session="fetch")
                session.commit()
                return ExecuteResult(success=True, affected_rows=affected_rows)
        except Exception as e:
            logger.error("Update operation failed", error=str(e))
            raise

    @ToolRegistry.register_tool_action(description="Delete data from the database")
    async def delete(self, params: DeleteParams[T]) -> ExecuteResult:
        """Delete records from the specified table"""
        try:
            with self.session() as session:
                query = session.query(params.model).filter_by(**params.where)
                affected_rows = query.delete(synchronize_session="fetch")
                session.commit()
                return ExecuteResult(success=True, affected_rows=affected_rows)
        except Exception as e:
            logger.error("Delete operation failed", error=str(e))
            raise
