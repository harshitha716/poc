import os
from typing import Dict, List

import structlog

from pantheon.ai_agents.internal.llm_service.service import LLMService
from pantheon.utils.utils import extract_yaml_from_response
from pantheon.ai_agents.internal.llm_service.enums.llmclient import (
    LLMModel,
    Role,
    ContentType,
)
from pantheon.ai_agents.agents.herm_formula_agent.schemas.formula_agent import (
    HermFormulaAgentResponse,
)
from pantheon.ai_agents.agents.herm_formula_agent.constants.herm_formula_constants import (
    SYSTEM_PROMPT_FILE_PATH,
    FORMULA_NOT_FOUND,
    FORMULA_NOT_FOUND_EXPLANATION,
    PARSED_FORMULA,
    FORMULA_DICT_KEY,
    EXPLANATION_DICT_KEY,
)
from pantheon.ai_agents.internal.llm_service.enums.llmclient import LLMClientType
from pantheon.ai_agents.tools.herm.tool import HermTool

logger = structlog.get_logger(__name__)


class HermFormulaAgent:
    def __init__(self):
        self.llm_service = LLMService(client_type=LLMClientType.ANTHROPIC)
        self.herm_tool = HermTool()
        self.system_prompt = self._load_system_prompt()

    @staticmethod
    def _load_system_prompt() -> str:
        filepath = os.path.join(os.path.dirname(__file__), SYSTEM_PROMPT_FILE_PATH)
        try:
            with open(filepath, "r") as file:
                return file.read()
        except FileNotFoundError as e:
            logger.exception(
                "HERM_FORMULA_AGENT_ERROR_LOADING_SYSTEM_PROMPT", exception=str(e)
            )
            raise

    def process_user_input(self, query: str, context: Dict) -> HermFormulaAgentResponse:
        try:
            herm_formula_prompt_messages = self._create_herm_formula_prompt(
                query, context
            )
            response = self._query_llm_service(herm_formula_prompt_messages)
            logger.info("HERM_FORMULA_RAW_LLM_RESPONSE", response=response)
            processed_response = extract_yaml_from_response(response)
            formula_llm_response = self._parse_llm_response(processed_response)
            return formula_llm_response
        except Exception as e:
            logger.exception(
                "HERM_FORMULA_AGENT_ERROR_PROCESSING_USER_INPUT",
                query=query,
                exception=str(e),
            )
            return HermFormulaAgentResponse(
                formula="", explanation="Sorry we couldn't fulfil your request"
            )

    def _create_herm_formula_prompt(
        self, query: str, context: Dict
    ) -> List[Dict[str, str]]:
        functions = self.herm_tool.get_herm_formulas()
        system_content = self.system_prompt.replace("{{USER_QUERY}}", query)
        system_content = system_content.replace("{{FUNCTION_LIBRARY}}", functions)
        system_content = system_content.replace("{{CONTEXT}}", str(context))

        return [
            {Role.ROLE: Role.USER, ContentType.CONTENT: system_content},
        ]

    def _query_llm_service(self, messages: List[Dict[str, str]]) -> str:
        try:
            response = self.llm_service.send_message(
                messages=messages, model=str(LLMModel.Claude3_5Sonnet)
            )
            return response.content
        except Exception as e:
            logger.exception(
                "HERM_FORMULA_AGENT_ERROR_QUERYING_LLM_SERVICE",
                error=str(e),
            )
            raise

    def _parse_llm_response(self, response_dict) -> HermFormulaAgentResponse:
        if response_dict is None:
            return HermFormulaAgentResponse(
                formula=FORMULA_NOT_FOUND,
                explanation=FORMULA_NOT_FOUND_EXPLANATION,
            )
        formula = response_dict.get(FORMULA_DICT_KEY, FORMULA_NOT_FOUND)
        decorated_formula = self._decorate_formula(formula)
        herm_formula_agent_response = HermFormulaAgentResponse(
            formula=decorated_formula,
            explanation=response_dict.get(EXPLANATION_DICT_KEY, ""),
        )
        logger.info("HERM_FORMULA_AGENT_RESPONSE", response=response_dict)
        return herm_formula_agent_response

    def _decorate_formula(self, formula: str) -> str:
        if formula != FORMULA_NOT_FOUND:
            return PARSED_FORMULA.format(formula)
        return formula
