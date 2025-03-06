from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class AnalyzeStatementInput(BaseModel):
    column_mapping: List[Dict[str, Any]]
    sample_data_csv: str
    amount_column_name: str
    amount_column_region: str


class AnalyzeStatementOutput(BaseModel):
    analysis_result: Optional[Dict[str, Any]]
