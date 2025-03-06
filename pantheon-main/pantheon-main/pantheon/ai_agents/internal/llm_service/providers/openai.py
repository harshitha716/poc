from openai import OpenAI
from typing import Dict
from pantheon.ai_agents.internal.llm_service.schemas.llm import LLMMessageResponse
from pantheon.ai_agents.internal.llm_service.providers.llmclient import LLMClient
from pantheon.ai_agents.internal.llm_service.exceptions import NoLLMResponse

import structlog
from pantheon.settings.settings import Settings
import asyncio

logger = structlog.get_logger(__name__)


class OpenAIClient(LLMClient):
    """
    A client class for interacting with OpenAI's Chat Completion API.
    """

    def __init__(self):
        self.client = OpenAI(api_key=Settings.OPENAI_API_KEY)

    def send_message(
        self, messages: list[Dict[str, str]], model="gpt-3.5-turbo"
    ) -> LLMMessageResponse:
        """
        Sends a message to the OpenAI Chat Completion API synchronously.
        """

        logger.info("OPEN_AI_SEND_MESSAGE", model=model, messages=messages)
        try:
            response = self.client.chat.completions.create(
                model=model, messages=messages
            )
        except Exception as e:
            logger.exception("OPEN_AI_SEND_MESSAGE_API_CALL_ERROR", error=e)
            raise e

        logger.info(
            "OPEN_AI_SEND_MESSAGE_RESPONSE",
            model=model,
            response=response,
        )

        if not response.choices:
            logger.info(
                "OPEN_AI_SEND_MESSAGE_NO_RESPONSE",
                model=model,
                messages=messages,
                response=response,
            )
            return NoLLMResponse("No response from OpenAI")

        return LLMMessageResponse(
            content=response.choices[0].message.content,
            role=response.choices[0].message.role,
        )

    async def send_message_async(
        self, messages: list[Dict[str, str]], model="gpt-3.5-turbo"
    ) -> LLMMessageResponse:
        """
        Sends a message to the OpenAI Chat Completion API asynchronously.
        """
        logger.info("OPEN_AI_SEND_MESSAGE_ASYNC", model=model, messages=messages)
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create, model=model, messages=messages
            )
        except Exception as e:
            logger.exception("OPEN_AI_SEND_MESSAGE_ASYNC_API_CALL_ERROR", error=e)
            raise e

        logger.info(
            "OPEN_AI_SEND_MESSAGE_ASYNC_RESPONSE",
            model=model,
            response=response,
        )

        if not response.choices:
            logger.info(
                "OPEN_AI_SEND_MESSAGE_ASYNC_NO_RESPONSE",
                model=model,
                messages=messages,
                response=response,
            )
            return NoLLMResponse("No response from OpenAI")

        return LLMMessageResponse(
            content=response.choices[0].message.content,
            role=response.choices[0].message.role,
        )
