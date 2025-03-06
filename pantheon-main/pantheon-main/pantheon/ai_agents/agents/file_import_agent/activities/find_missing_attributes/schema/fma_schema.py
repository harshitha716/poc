from pydantic import BaseModel
from typing import List, Any
import pandas as pd


class FindMissingAttributesInput(BaseModel):
    original_df: pd.DataFrame
    region: str
    unmapped_attributes: List[str]

    class Config:
        arbitrary_types_allowed = True


class FindMissingAttributesOutput(BaseModel):
    mapped_attributes: List[Any]
    search_still_unmapped: List[str]
    opening_balance: Any
