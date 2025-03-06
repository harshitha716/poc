import pytest
from unittest.mock import AsyncMock, patch
from pantheon.ai_agents.agents.file_import_agent.activities.get_regex_patterns.grp import (
    get_regex_patterns_activity,
)
from pantheon.ai_agents.agents.file_import_agent.activities.get_regex_patterns.schema.grp_schema import (
    RegexPatternsInput,
    RegexPatternsOutput,
)
from pantheon.ai_agents.agents.file_import_agent.activities.get_regex_patterns.helpers.grp_helpers import (
    GetRegexPatternsAgent,
)
from pantheon.ai_agents.internal.llm_service.enums.llmclient import Role, ContentType


@pytest.fixture
def mock_llm_response():
    return AsyncMock(
        content=r"""Certainly! I'll analyze the given grouped values and create regex patterns for identifying credit and debit transactions. Let's go through this step-by-step:

1. Analysis of the grouped values:
   - "Credit" and "CR" clearly indicate credit transactions
   - "Debit" and "DR" clearly indicate debit transactions

2. Chain-of-thought reasoning:
   - Credits: "Credit" and "CR" are straightforward indicators of credit transactions
   - Debits: "Debit" and "DR" are clear indicators of debit transactions
   - There are no ambiguous terms in this set
   - We observe that both full words ("Credit", "Debit") and abbreviations ("CR", "DR") are used

3. Creating regex patterns:
   - For credits, we need to match "Credit" and "CR"
   - For debits, we need to match "Debit" and "DR"
   - We'll use the '^' and '$' anchors to ensure full string matching
   - We'll use the '|' operator to combine conditions
   - We'll make the patterns case-insensitive using (?i)

4. Ensuring mutual exclusivity and flexibility:
   - The patterns are naturally mutually exclusive as they match different terms
   - We don't need to use character classes or \s* in this case, as the terms are distinct and don't contain spaces

Based on this analysis, here are the regex patterns in the requested JSON format:

<output>
{
    "regex_credit": "(?i)^(Credit|CR)$",
    "regex_debit": "(?i)^(Debit|DR)$"
}
</output>

These patterns will match the given terms exactly, regardless of case, and will not overlap with each other. They are simple and effective for the provided grouped values."""
    )


@pytest.mark.asyncio
async def test_get_regex_patterns_activity_success(mock_llm_response):
    with patch(
        "pantheon.ai_agents.agents.file_import_agent.activities.get_regex_patterns.helpers.grp_helpers.LLMService.send_message_async",
        return_value=mock_llm_response,
    ):
        input_data = RegexPatternsInput(grouped_values_str="Credit,Debit,CR,DR")
        result = await get_regex_patterns_activity(input_data)

        assert isinstance(result, RegexPatternsOutput)
        assert result.regex_credit == "(?i)^(Credit|CR)$"
        assert result.regex_debit == "(?i)^(Debit|DR)$"


@pytest.mark.asyncio
async def test_get_regex_patterns_activity_failure(mock_llm_response):
    with patch(
        "pantheon.ai_agents.agents.file_import_agent.activities.get_regex_patterns.helpers.grp_helpers.LLMService.send_message_async",
        return_value=AsyncMock(content="Invalid response"),
    ):
        input_data = RegexPatternsInput(grouped_values_str="Credit,Debit,CR,DR")
        with pytest.raises(ValueError, match="Failed to generate regex patterns"):
            await get_regex_patterns_activity(input_data)


@pytest.mark.asyncio
async def test_get_regex_patterns_agent_init():
    agent = GetRegexPatternsAgent()
    assert agent.llm_service is not None
    assert agent.system_prompt is not None


@pytest.mark.asyncio
async def test_get_regex_patterns_agent_prepare_llm_message():
    agent = GetRegexPatternsAgent()
    grouped_values_str = "Credit,Debit,CR,DR"
    message = agent._prepare_llm_message(grouped_values_str)
    assert grouped_values_str in message


@pytest.mark.asyncio
async def test_get_regex_patterns_agent_create_messages():
    agent = GetRegexPatternsAgent()
    llm_message = "System message"
    grouped_values_str = "Credit,Debit,CR,DR"
    messages = agent._create_messages(llm_message, grouped_values_str)
    assert len(messages) == 2
    assert messages[0][Role.ROLE] == Role.SYSTEM
    assert messages[1][Role.ROLE] == Role.USER
    assert grouped_values_str in messages[1][ContentType.CONTENT]


@pytest.mark.asyncio
async def test_get_regex_patterns_agent_process_llm_response_success(mock_llm_response):
    agent = GetRegexPatternsAgent()
    result = agent._process_llm_response(mock_llm_response.content)
    assert isinstance(result, dict)
    assert "regex_credit" in result
    assert "regex_debit" in result


@pytest.mark.asyncio
async def test_get_regex_patterns_agent_process_llm_response_failure():
    agent = GetRegexPatternsAgent()
    with pytest.raises(ValueError, match="No <output> tags found in LLM response"):
        agent._process_llm_response("Invalid response")


@pytest.mark.asyncio
async def test_get_regex_patterns_agent_extract_patterns_directly():
    agent = GetRegexPatternsAgent()
    json_str = '"regex_credit": "(?i)^(Credit|CR)$", "regex_debit": "(?i)^(Debit|DR)$"'
    result = agent._extract_patterns_directly(json_str)
    assert isinstance(result, dict)
    assert result["regex_credit"] == "(?i)^(Credit|CR)$"
    assert result["regex_debit"] == "(?i)^(Debit|DR)$"


@pytest.mark.asyncio
async def test_get_regex_patterns_agent_validate_regex_patterns_success():
    agent = GetRegexPatternsAgent()
    response_json = {
        "regex_credit": "(?i)^(Credit|CR)$",
        "regex_debit": "(?i)^(Debit|DR)$",
    }
    agent._validate_regex_patterns(response_json)  # Should not raise an exception


@pytest.mark.asyncio
async def test_get_regex_patterns_agent_validate_regex_patterns_failure():
    agent = GetRegexPatternsAgent()
    response_json = {"regex_credit": "(?i)^(Credit|CR)$"}  # Missing regex_debit
    with pytest.raises(ValueError, match="Missing regex patterns in LLM response"):
        agent._validate_regex_patterns(response_json)


@pytest.mark.parametrize(
    "input_str, expected_output",
    [
        # Test case 1: Valid JSON input
        (
            '{"regex_credit": "(?i)^(Credit|CR)$", "regex_debit": "(?i)^(Debit|DR)$"}',
            {"regex_credit": "(?i)^(Credit|CR)$", "regex_debit": "(?i)^(Debit|DR)$"},
        ),
        # Test case 2: Invalid JSON, fallback to direct extraction
        (
            '"regex_credit": "(?i)^(Credit|CR)$", "regex_debit": "(?i)^(Debit|DR)$"',
            {"regex_credit": "(?i)^(Credit|CR)$", "regex_debit": "(?i)^(Debit|DR)$"},
        ),
    ],
)
def test_parse_json_or_extract_patterns(input_str, expected_output):
    agent = GetRegexPatternsAgent()
    result = agent._parse_json_or_extract_patterns(input_str)
    assert result == expected_output


@pytest.mark.asyncio
async def test_parse_json_or_extract_patterns_invalid_input():
    agent = GetRegexPatternsAgent()
    invalid_input = "This is not a valid JSON or pattern string"
    with pytest.raises(
        ValueError, match="Failed to extract regex patterns from LLM response"
    ):
        agent._parse_json_or_extract_patterns(invalid_input)


# pytest --cov=pantheon.ai_agents.agents.file_import_agent.activities.get_regex_patterns --cov-report=term-missing --cov-report=html pantheon/ai_agents/agents/file_import_agent/activities/get_regex_patterns/tests/test_grp.py -v
