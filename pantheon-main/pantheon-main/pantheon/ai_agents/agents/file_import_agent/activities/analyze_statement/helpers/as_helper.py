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
from ..constants.as_constants import ANALYZE_STATEMENT_PROMPT_PATH
import structlog

logger = structlog.get_logger(__name__)


class AnalyzeStatementHelper:
    def __init__(self):
        self.llm_service = LLMService(client_type=LLMClientType.ANTHROPIC)
        self.system_prompt = self._load_file_content(ANALYZE_STATEMENT_PROMPT_PATH)

    @staticmethod
    def _load_file_content(file_path: str) -> str:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        correct_path = os.path.join(
            current_dir, "..", "static", os.path.basename(file_path)
        )

        with open(correct_path, "r", encoding="utf-8") as file:
            return file.read()

    async def analyze_statement(
        self,
        column_mapping: str,
        sample_data_csv: str,
        amount_column_name: str,
        amount_column_region: str,
    ) -> dict:
        try:
            llm_message = self.system_prompt

            messages = [
                {Role.ROLE: Role.SYSTEM, ContentType.CONTENT: llm_message},
                {
                    Role.ROLE: Role.USER,
                    ContentType.CONTENT: f"""
                        Inputs:
                        1. Column Mapping:
                        <column_mapping_example>
                        {column_mapping}
                        </column_mapping_example>

                        2. Sample Data (first few rows):
                        <sample_data_example>
                        {sample_data_csv}
                        </sample_data_example>

                        3. Amount Column Information:
                        Column Name: {amount_column_name}
                        Column Region: {amount_column_region}
                    """,
                },
            ]

            response = await self.llm_service.send_message_async(
                messages=messages, model=str(LLMModel.Claude3_5Sonnet)
            )

            response_text = response.content
            json_match = re.search(r"<output>(.*?)</output>", response_text, re.DOTALL)

            if json_match:
                json_str = json_match.group(1)
                try:
                    response_json = json.loads(json_str)
                    return response_json
                except json.JSONDecodeError:
                    logger.error("Invalid JSON in LLM response")
                    return None
            else:
                logger.error("No <output> tags found in LLM response")
                return None

        except Exception as e:
            logger.error("Error in analyze_statement", error=str(e))
            return None
