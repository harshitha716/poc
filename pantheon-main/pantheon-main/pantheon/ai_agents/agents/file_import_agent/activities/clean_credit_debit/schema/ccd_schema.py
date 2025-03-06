from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, ConfigDict
import pandas as pd


class CleanCreditDebitInput(BaseModel):
    df: pd.DataFrame
    column_mapping: List[Any]
    unmapped_attributes: List[str]

    model_config = ConfigDict(arbitrary_types_allowed=True)


class AnalysisResult(BaseModel):
    value_region: str
    type_region: Optional[str] = None


class RegexPatterns(BaseModel):
    regex_credit: str
    regex_debit: str


class RegexConfig(BaseModel):
    amount_column_region: str
    type_region: Optional[str]
    regex_credit: str
    regex_debit: str


class CleanCreditDebitResult(BaseModel):
    cb: Union[RegexConfig, Dict[str, Any]]
    unmapped_attributes: List[Any]
