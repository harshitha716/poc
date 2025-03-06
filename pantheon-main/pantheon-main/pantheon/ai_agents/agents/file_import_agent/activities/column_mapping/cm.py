import pandas as pd
from typing import List
from .helpers.cm_helper import ColumnMappingAgent
from .schema.cm_schema import ColumnMappingResult, ColumnInfo


async def column_mapping_activity(
    island_df: pd.DataFrame, column_info: List[ColumnInfo], original_df: pd.DataFrame
) -> ColumnMappingResult:
    agent = ColumnMappingAgent()
    mapped_columns, unmapped_attributes, errors = await agent.get_column_mappings(
        island_df, [ci.dict() for ci in column_info], original_df
    )

    return ColumnMappingResult(
        mapped_columns=mapped_columns,
        unmapped_attributes=unmapped_attributes,
        errors=errors,
    )
