from pantheon.ai_agents.agent_service import AgentService
from pantheon.ai_agents.schemas.agent_schema import (
    AgentQueryResponse,
    TransformationsActionsResponse,
)
import structlog
import uuid

logger = structlog.get_logger(__name__)


class ChatController:
    def __init__(self):
        self.agent_service = AgentService()

    def get_herm_formula(
        self, query: str, page_id: uuid.UUID, sheet_id: int
    ) -> AgentQueryResponse:
        agent_response = self.agent_service.get_herm_formula(
            page_id=page_id, sheet_id=sheet_id, query=query
        )
        logger.info("AGENT_SERVICE_RESPONSE", agent_response=agent_response)

        return agent_response

    def get_herm_transformations(
        self, query: str, page_id: uuid.UUID, sheet_id: int
    ) -> TransformationsActionsResponse:
        agent_response = self.agent_service.get_herm_transformations_actions(
            page_id=page_id, sheet_id=sheet_id, query=query
        )
        logger.info(
            "AGENT_SERVICE_TRANSFORMATIONS_RESPONSE", agent_response=agent_response
        )

        return agent_response
