import io
import json
import pandas as pd
from pantheon.ai_agents.tools.clean_credit_debit.tool import (
    group_csv_column,
    group_field_amount_patterns,
)
from ..schema.ccd_schema import AnalysisResult


def prepare_grouped_values(df: pd.DataFrame, analysis_result: AnalysisResult) -> str:
    if analysis_result["type_region"]:
        grouped_values = group_csv_column(df, analysis_result["type_region"])
        return ", ".join(f"'{value}'" for value in grouped_values)
    else:
        grouped_patterns = group_field_amount_patterns(
            df, analysis_result["value_region"]
        )
        return json.dumps([pattern.dict() for pattern in grouped_patterns])


def get_sample_data_csv(df: pd.DataFrame) -> str:
    csv_buffer = io.StringIO()
    df.head(10).to_csv(csv_buffer, index=False, header=None)
    return csv_buffer.getvalue()
