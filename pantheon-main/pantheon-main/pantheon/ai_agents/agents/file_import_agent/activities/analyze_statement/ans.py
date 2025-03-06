from pantheon.ai_agents.agents.file_import_agent.activities.analyze_statement.helpers.as_helper import (
    AnalyzeStatementHelper,
)
from pantheon.ai_agents.agents.file_import_agent.activities.analyze_statement.schema.as_schema import (
    AnalyzeStatementInput,
    AnalyzeStatementOutput,
)


async def analyze_statement_activity(
    input_data: AnalyzeStatementInput,
) -> AnalyzeStatementOutput:
    helper = AnalyzeStatementHelper()
    result = await helper.analyze_statement(
        input_data.column_mapping,
        input_data.sample_data_csv,
        input_data.amount_column_name,
        input_data.amount_column_region,
    )
    return result
