from pydantic import BaseModel, Field
from typing import List, Any


class ColumnMapping(BaseModel):
    name: str
    type: str
    region: str
    mapped_attribute: str
    attribute_type: Any


class LLMResponse(BaseModel):
    mapped_columns: List[Any] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class ColumnMappingResult(BaseModel):
    mapped_columns: List[Any]
    unmapped_attributes: List[str]
    errors: List[str]


class ColumnInfo(BaseModel):
    name: str
    type: str
    region: str
