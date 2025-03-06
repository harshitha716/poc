import json
import re
import os
from pantheon.ai_agents.internal.llm_service.enums.llmclient import (
    LLMClientType,
    LLMModel,
    ContentType,
    Role,
)
from pantheon.ai_agents.internal.llm_service.service import LLMService
from pantheon.ai_agents.agents.file_import_agent.activities.get_regex_patterns.constants.grp_constants import (
    GET_REGEX_PATTERNS_PROMPT_PATH,
    REGEX_CREDIT_PATTERN,
    REGEX_DEBIT_PATTERN,
)

import structlog

logger = structlog.get_logger(__name__)


class GetRegexPatternsAgent:
    def __init__(self):
        self.llm_service = LLMService(client_type=LLMClientType.ANTHROPIC)
        self.system_prompt = self._load_file_content(GET_REGEX_PATTERNS_PROMPT_PATH)

    @staticmethod
    def _load_file_content(file_path: str) -> str:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        correct_path = os.path.join(
            current_dir, "..", "static", os.path.basename(file_path)
        )

        with open(correct_path, "r", encoding="utf-8") as file:
            return file.read()

    async def get_regex_patterns(self, grouped_values_str: str) -> dict:
        try:
            llm_message = self._prepare_llm_message(grouped_values_str)
            messages = self._create_messages(llm_message, grouped_values_str)
            response = await self._get_llm_response(messages)
            return self._process_llm_response(response.content)
        except Exception as e:
            logger.error(f"Error in get_regex_patterns: {str(e)}")
            return None

    def _prepare_llm_message(self, grouped_values_str: str) -> str:
        return self.system_prompt.replace("{GROUPED_VALUES}", grouped_values_str)

    def _create_messages(self, llm_message: str, grouped_values_str: str) -> list:
        return [
            {Role.ROLE: Role.SYSTEM, ContentType.CONTENT: llm_message},
            {
                Role.ROLE: Role.USER,
                ContentType.CONTENT: f"Please generate the regex patterns based on these grouped values: [{grouped_values_str}]",
            },
        ]

    async def _get_llm_response(self, messages: list):
        return await self.llm_service.send_message_async(
            messages=messages, model=str(LLMModel.Claude3_5Sonnet)
        )

    def _process_llm_response(self, response_text: str) -> dict:
        json_str = self._extract_json_from_output(response_text)
        response_json = self._parse_json_or_extract_patterns(json_str)
        self._validate_regex_patterns(response_json)
        return response_json

    def _extract_json_from_output(self, response_text: str) -> str:
        json_match = re.search(r"<output>(.*?)</output>", response_text, re.DOTALL)
        if not json_match:
            raise ValueError("No <output> tags found in LLM response")
        return json_match.group(1).strip()

    def _parse_json_or_extract_patterns(self, json_str: str) -> dict:
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return self._extract_patterns_directly(json_str)

    def _extract_patterns_directly(self, json_str: str) -> dict:
        credit_match = re.search(REGEX_CREDIT_PATTERN, json_str)
        debit_match = re.search(REGEX_DEBIT_PATTERN, json_str)

        if credit_match and debit_match:
            return {
                "regex_credit": credit_match.group(1),
                "regex_debit": debit_match.group(1),
            }
        else:
            raise ValueError("Failed to extract regex patterns from LLM response")

    def _validate_regex_patterns(self, response_json: dict):
        if "regex_credit" not in response_json or "regex_debit" not in response_json:
            raise ValueError("Missing regex patterns in LLM response")
