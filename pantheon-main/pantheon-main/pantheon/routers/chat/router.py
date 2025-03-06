from fastapi import APIRouter
from pantheon.routers.chat.schemas.chat import ChatResponse, ChatRequest

from pantheon.chat import chat_controller
from pantheon.ai_agents.schemas.agent_schema import (
    AgentQueryResponse,
    TransformationsActionsResponse,
)


router = APIRouter(prefix="/chat")


@router.post("")
def chat(chat_request: ChatRequest) -> ChatResponse:
    response: AgentQueryResponse = chat_controller.get_herm_formula(
        chat_request.query,
        chat_request.page_request.page_id,
        chat_request.page_request.sheet_id,
    )
    return ChatResponse(
        status=response.status,
        action=response.action,
        content=response.content,
        explanation=response.explanation,
    )


@router.post("/transformations")
def transformations(chat_request: ChatRequest) -> TransformationsActionsResponse:
    response: TransformationsActionsResponse = chat_controller.get_herm_transformations(
        chat_request.query,
        chat_request.page_request.page_id,
        chat_request.page_request.sheet_id,
    )
    return response
