import os
import json

import structlog
import uuid
from typing import Dict
from pantheon.ai_agents.agents.herm_formula_agent.herm_formula_agent import (
    HermFormulaAgent,
)
from pantheon.ai_agents.agents.herm_transformation_agent.herm_transformation_agent import (
    HermTransformationAgent,
)
from pantheon.ai_agents.agents.herm_formula_agent.schemas.formula_agent import (
    HermFormulaAgentResponse,
)
from pantheon.ai_agents.schemas.agent_schema import (
    AgentQueryResponse,
    TransformationsActionsResponse,
)
from pantheon.ai_agents.constants.agent_service_enums import Actions, Status

from pantheon.ai_agents.agents.herm_formula_agent.constants.herm_formula_constants import (
    FORMULA_NOT_FOUND,
)
from pantheon import settings
from pantheon.ai_agents.tools.herm.tool import HermTool

logger = structlog.get_logger(__name__)


class AgentService:
    def __init__(self):
        self.herm_formula_agent = HermFormulaAgent()
        self.herm_transformation_agent = HermTransformationAgent()
        self.herm_tool = HermTool()
        self.env = settings.ENVIRONMENT

    @staticmethod
    def _load_context() -> Dict:
        filepath = os.path.join(os.path.dirname(__file__), "context.json")
        try:
            with open(filepath, "r") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error("HERM_FORMULA_AGENT_ERROR_LOADING_FUNCTIONS", error=str(e))
            raise

    def get_herm_formula(
        self, query: str, page_id: uuid.UUID, sheet_id: int
    ) -> AgentQueryResponse:
        sheet_context = self.herm_tool.get_sheet_context(page_id, sheet_id)
        response = self.herm_formula_agent.process_user_input(query, sheet_context)
        parsed_response = self._parse_herm_formula_response(response)
        return parsed_response

    def _parse_herm_formula_response(
        self, response: HermFormulaAgentResponse
    ) -> AgentQueryResponse:
        status = (
            Status.FAILED if FORMULA_NOT_FOUND in response.formula else Status.SUCCESS
        )
        return AgentQueryResponse(
            status=status,
            action=Actions.GET_HERM_FORMULA,
            content=response.formula,
            explanation=response.explanation,
        )

    def get_herm_transformations_actions(
        self, query: str, page_id: uuid.UUID, sheet_id: int
    ) -> TransformationsActionsResponse:
        response = self.herm_transformation_agent.get_herm_transformations(
            query, page_id, sheet_id
        )
        return response
