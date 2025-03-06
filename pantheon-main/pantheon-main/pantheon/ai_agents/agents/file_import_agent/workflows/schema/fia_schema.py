from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class AddCreditDebitConfig(BaseModel):
    amount_column_region: str
    type_region: Optional[str] = None
    regex_credit: str
    regex_debit: str


class ColumnInfo(BaseModel):
    name: str
    type: str
    region: str


class ColumnMapping(BaseModel):
    name: str
    mapped_attribute: str
    attribute_type: str


class Action(BaseModel):
    type: str
    config: Dict[str, Any]


class TransformationConfig(BaseModel):
    actions: List[Action]


class ConfigResponse(BaseModel):
    transformation_config: TransformationConfig
    unmapped_columns: Optional[List[str]] = None
    errors: Optional[List[str]] = None
    opening_balance: Optional[dict] = None
