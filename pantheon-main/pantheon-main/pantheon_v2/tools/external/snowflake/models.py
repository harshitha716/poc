from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Union, Type


class QueryParams[T](BaseModel):
    query: str = Field(..., description="SQL query to execute")
    parameters: Optional[Dict[str, Any]] = Field(
        None, description="Query parameters for parameterized queries"
    )
    model: Type[T] = Field(..., description="Model to use for the query")


class InsertParams[T](BaseModel):
    table: str = Field(..., description="Table name to insert into")
    values: Union[Dict[str, Any], List[Dict[str, Any]]] = Field(
        ..., description="Single record or list of records to insert"
    )
    model: Type[T] = Field(..., description="Model to use for the insert")


class UpdateParams[T](BaseModel):
    table: str = Field(..., description="Table name to update")
    values: Dict[str, Any] = Field(..., description="Values to update")
    where: Dict[str, Any] = Field(..., description="Where clause conditions")
    model: Type[T] = Field(..., description="Model to use for the update")


class DeleteParams[T](BaseModel):
    table: str = Field(..., description="Table name to delete from")
    where: Dict[str, Any] = Field(..., description="Where clause conditions")
    model: Type[T] = Field(..., description="Model to use for the delete")


class QueryResult(BaseModel):
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int


class ExecuteResult(BaseModel):
    success: bool
    affected_rows: int
