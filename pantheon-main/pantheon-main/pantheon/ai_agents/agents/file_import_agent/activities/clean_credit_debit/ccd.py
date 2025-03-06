from .schema.ccd_schema import CleanCreditDebitInput, CleanCreditDebitResult
from .helpers.ccd_helper import clean_credit_debit_columns


async def clean_credit_debit_activity(
    input_data: CleanCreditDebitInput,
) -> CleanCreditDebitResult:
    # The input_data is already validated by Pydantic
    result = await clean_credit_debit_columns(
        input_data.df, input_data.column_mapping, input_data.unmapped_attributes
    )
    return result
