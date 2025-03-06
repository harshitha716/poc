from typing import Any, List
import pandas as pd
from pantheon.ai_agents.agents.file_import_agent.activities.analyze_statement.ans import (
    analyze_statement_activity,
)
from pantheon.ai_agents.agents.file_import_agent.activities.get_regex_patterns.grp import (
    get_regex_patterns_activity,
)
from ..schema.ccd_schema import CleanCreditDebitResult, RegexConfig
from .ccd_tools import prepare_grouped_values, get_sample_data_csv
from pantheon.ai_agents.agents.file_import_agent.activities.analyze_statement.schema.as_schema import (
    AnalyzeStatementInput,
)
from pantheon.ai_agents.agents.file_import_agent.activities.get_regex_patterns.schema.grp_schema import (
    RegexPatternsInput,
)
from ..constants.ccd_constants import CREDIT, DEBIT

import structlog

logger = structlog.get_logger(__name__)


async def clean_credit_debit(
    df: pd.DataFrame,
    column_mapping: List[Any],
    amount_column_name: str,
    amount_column_region: str,
) -> RegexConfig:
    try:
        # Get sample data CSV
        sample_data_csv = get_sample_data_csv(df)

        # Use column_mapping directly without converting to dict
        analysis_result = await analyze_statement_activity(
            AnalyzeStatementInput(
                column_mapping=column_mapping,
                sample_data_csv=sample_data_csv,
                amount_column_name=amount_column_name,
                amount_column_region=amount_column_region,
            )
        )

        parameters = analysis_result["parameters"]

        # Prepare grouped values
        grouped_values_str = prepare_grouped_values(df, parameters)

        # Get regex patterns using the function
        regex_patterns = await get_regex_patterns_activity(
            RegexPatternsInput(grouped_values_str=grouped_values_str)
        )

        return RegexConfig(
            amount_column_region=parameters["value_region"],
            type_region=parameters["type_region"],
            regex_credit=regex_patterns.regex_credit,
            regex_debit=regex_patterns.regex_debit,
        )

    except Exception as e:
        logger.error(f"An error occurred in clean_credit_debit: {e}")
        return RegexConfig(
            amount_column_region="",
            type_region="",
            regex_credit="",
            regex_debit="",
        )


async def clean_credit_debit_columns(
    original_df: pd.DataFrame, column_mapping: List, unmapped_attributes: List
) -> CleanCreditDebitResult:
    cb = {}
    if CREDIT in unmapped_attributes or DEBIT in unmapped_attributes:
        try:
            transaction_amount_item = next(
                item
                for item in column_mapping
                if item["mapped_attribute"] == "transaction_amount"
            )
        except StopIteration:
            return CleanCreditDebitResult(
                cb={}, unmapped_attributes=unmapped_attributes
            )

        amount_column_name = transaction_amount_item["name"]
        amount_column_region = transaction_amount_item["region"]

        cb = await clean_credit_debit(
            original_df,
            column_mapping,
            amount_column_name,
            amount_column_region,
        )

        column_mapping.remove(transaction_amount_item)
        unmapped_attributes = [
            attr for attr in unmapped_attributes if attr not in [CREDIT, DEBIT]
        ]
    return CleanCreditDebitResult(cb=cb, unmapped_attributes=unmapped_attributes)
