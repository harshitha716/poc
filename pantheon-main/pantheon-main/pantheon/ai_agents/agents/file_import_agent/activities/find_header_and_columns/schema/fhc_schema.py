from pydantic import BaseModel
from typing import List, Optional
import pandas as pd


class FindHeaderAndColumnsInput(BaseModel):
    island_df: pd.DataFrame
    region: str
    start_row: int

    class Config:
        arbitrary_types_allowed = True


class ColumnInfo(BaseModel):
    name: str
    type: str
    region: str


class FindHeaderAndColumnsOutput(BaseModel):
    header_row_index: int
    header_columns: List[str]
    new_region: str
    new_start_row: int
    column_info: List[ColumnInfo]
    updated_df: Optional[pd.DataFrame]

    class Config:
        arbitrary_types_allowed = True
