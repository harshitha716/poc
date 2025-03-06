from pantheon.ai_agents.agents.file_import_agent.activities.get_regex_patterns.helpers.grp_helpers import (
    GetRegexPatternsAgent,
)
from pantheon.ai_agents.agents.file_import_agent.activities.get_regex_patterns.schema.grp_schema import (
    RegexPatternsInput,
    RegexPatternsOutput,
)


async def get_regex_patterns_activity(
    input_data: RegexPatternsInput,
) -> RegexPatternsOutput:
    """
    Temporal activity to get regex patterns based on grouped values.

    Args:
        input_data (RegexPatternsInput): Input data containing grouped values string.

    Returns:
        RegexPatternsOutput: A dictionary containing regex patterns for credit and debit.
    """
    agent = GetRegexPatternsAgent()
    result = await agent.get_regex_patterns(input_data.grouped_values_str)

    if result is None:
        raise ValueError("Failed to generate regex patterns")

    return RegexPatternsOutput(**result)
