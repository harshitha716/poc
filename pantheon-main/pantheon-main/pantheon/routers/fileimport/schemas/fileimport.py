from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class ColumnAttribute(BaseModel):
    column_number: int
    value: str


class ColumnAttributesRequest(BaseModel):
    attributes: List[ColumnAttribute]


class ColumnAttributesResponse(BaseModel):
    status: str
    chosen_field: Optional[str] = None
    data_type: Optional[str] = None
    explanation: Optional[str] = None
    column_number: Optional[int] = None


class CSVData(BaseModel):
    columns: List[int]
    index: List[int]
    data: List[List[Optional[Any]]]


class GenerateConfigRequest(BaseModel):
    csv_data: CSVData
    start_row: int
    template_config: Optional[Any] = None


class GenerateConfigResponse(BaseModel):
    status: str
    transformation_config: Optional[Dict[str, Any]] = None
    unmapped_columns: Optional[List[str]] = None
    errors: Optional[List[str]] = None
    opening_balance: Optional[Dict[str, Any]] = None
