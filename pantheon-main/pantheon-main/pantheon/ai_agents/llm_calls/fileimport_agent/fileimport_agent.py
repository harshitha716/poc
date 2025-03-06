import os
import re
import json
from typing import Dict, Optional, List

import structlog

from pantheon.ai_agents.internal.llm_service.service import LLMService
from pantheon.ai_agents.internal.llm_service.enums.llmclient import (
    LLMModel,
    Role,
    ContentType,
    LLMClientType,
)
from pantheon.ai_agents.llm_calls.fileimport_agent.constants.fileimport_agent_constants import (
    FIND_MANDATORY_COLUMN_FILE_PATH,
)

logger = structlog.get_logger(__name__)


class FindMandatoryField:
    def __init__(self):
        self.llm_service = LLMService(client_type=LLMClientType.ANTHROPIC)
        self.system_prompt = self._load_system_prompt()

    @staticmethod
    def _load_system_prompt() -> str:
        filepath = os.path.join(
            os.path.dirname(__file__), FIND_MANDATORY_COLUMN_FILE_PATH
        )
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                return file.read()
        except FileNotFoundError as e:
            logger.exception(
                "FILE_IMPORT_AGENT_ERROR_LOADING_SYSTEM_PROMPT", exception=str(e)
            )
            raise

    def _create_csv_analysis_prompt(self, row_values: str) -> str:
        return self.system_prompt.replace("{{row_values}}", row_values)

    async def analyze_csv_row(self, row_values: str) -> Optional[Dict]:
        try:
            prompt = self._create_csv_analysis_prompt(row_values)
            messages = self._create_messages(prompt)
            response = await self._query_llm_service(messages)
            processed_response = self._extract_json(response)
            return processed_response
        except Exception as e:
            logger.exception(
                "FILE_IMPORT_AGENT_ERROR_ANALYZING_CSV_ROW",
                row_values=row_values,
                exception=str(e),
            )
            return None

    def _create_messages(self, prompt: str) -> List[Dict[str, str]]:
        return [
            {Role.ROLE: Role.USER, ContentType.CONTENT: prompt},
        ]

    async def _query_llm_service(self, messages: List[Dict[str, str]]) -> str:
        try:
            response = await self.llm_service.send_message_async(
                messages=messages, model=str(LLMModel.Claude3_5Sonnet)
            )
            return response.content
        except Exception as e:
            logger.exception(
                "FILE_IMPORT_AGENT_ERROR_QUERYING_LLM_SERVICE",
                error=str(e),
            )
            raise

    @staticmethod
    def _extract_json(input_string: str) -> Optional[Dict]:
        output_pattern = r"<output>\s*(.*?)\s*</output>"
        match = re.search(output_pattern, input_string, re.DOTALL)

        if not match:
            return None

        output_content = match.group(1)
        start = output_content.find("{")
        end = output_content.rfind("}") + 1

        if start == -1 or end == 0:
            return None

        json_string = output_content[start:end]

        try:
            json_data = json.loads(json_string)
            return json_data
        except json.JSONDecodeError:
            return None
