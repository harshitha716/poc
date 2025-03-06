import structlog
from typing import Dict, List
from .enums.llmclient import LLMClientType
from .providers.openai import OpenAIClient
from .providers.anthropic import AnthropicClient
from .providers.llmclient import LLMClient
from .schemas.llm import LLMMessageResponse
from .exceptions import InvalidLLMClientType, NoLLMClientInitialised

logger = structlog.get_logger(__name__)


class LLMService:
    def __init__(self, client_type: str) -> None:
        self.client = self._get_llm_client(client_type)

    def _get_llm_client(self, client_type: str) -> LLMClient:
        match client_type:
            case LLMClientType.OPENAI:
                return OpenAIClient()
            case LLMClientType.ANTHROPIC:
                return AnthropicClient()
            case _:
                raise InvalidLLMClientType("Invalid LLM client type")

    def send_message(
        self, messages: List[Dict[str, str]], model: str
    ) -> LLMMessageResponse:
        if not self.client:
            logger.error("LLM_SEND_MESSAGE_FAILED", reason="No client initialized")
            raise NoLLMClientInitialised("No LLM client initialized")

        # Check if all messages are dictionaries
        if not all(isinstance(message, dict) for message in messages):
            raise TypeError("All messages must be dictionaries")

        send_message_response = self.client.send_message(messages, model)
        logger.info(
            "LLM_SEND_MESSAGE",
            model=model,
            messages=messages,
            response=send_message_response,
        )
        return send_message_response

    async def send_message_async(
        self, messages: List[Dict[str, str]], model: str
    ) -> LLMMessageResponse:
        if not self.client:
            logger.error("LLM_SEND_MESSAGE_FAILED", reason="No client initialized")
            raise NoLLMClientInitialised("No LLM client initialized")

        if not all(isinstance(message, dict) for message in messages):
            raise TypeError("All messages must be dictionaries")

        try:
            send_message_response = await self.client.send_message_async(
                messages, model
            )

            logger.info(
                "LLM_SEND_MESSAGE",
                model=model,
                messages=messages,
                response=send_message_response,
            )
            return send_message_response
        except Exception as e:
            logger.error("LLM_SEND_MESSAGE_FAILED", error=str(e))
            raise
