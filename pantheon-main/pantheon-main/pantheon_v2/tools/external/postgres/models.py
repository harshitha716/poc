from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Union


class QueryParams(BaseModel):
    query: str = Field(..., description="SQL query to execute")
    parameters: Optional[Dict[str, Any]] = Field(
        None, description="Query parameters for parameterized queries"
    )


class InsertParams(BaseModel):
    table: str = Field(..., description="Table name to insert into")
    values: Union[Dict[str, Any], List[Dict[str, Any]]] = Field(
        ..., description="Single record or list of records to insert"
    )


class UpdateParams(BaseModel):
    table: str = Field(..., description="Table name to update")
    values: Dict[str, Any] = Field(..., description="Values to update")
    where: Dict[str, Any] = Field(..., description="Where clause conditions")


class QueryResult(BaseModel):
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int


class ExecuteResult(BaseModel):
    success: bool
    affected_rows: int


class TableInsert(BaseModel):
    """Represents a single table insert operation"""

    table: str = Field(..., description="Table name to insert into")
    values: Dict[str, Any] = Field(..., description="record of values to insert")


class BatchInsertParams(BaseModel):
    """Parameters for batch insert operations across multiple tables"""

    operations: List[TableInsert] = Field(
        ..., description="List of insert operations to perform"
    )
