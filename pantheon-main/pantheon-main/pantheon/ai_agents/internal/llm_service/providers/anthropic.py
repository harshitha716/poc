import asyncio
import anthropic
from typing import Dict, List
from pantheon.ai_agents.internal.llm_service.schemas.llm import LLMMessageResponse
from pantheon.ai_agents.internal.llm_service.providers.llmclient import LLMClient
from pantheon.ai_agents.internal.llm_service.exceptions import NoLLMResponse
from pantheon.ai_agents.internal.llm_service.enums.llmclient import Role, ContentType

import structlog
from pantheon.settings.settings import Settings

logger = structlog.get_logger(__name__)


class AnthropicClient(LLMClient):
    """
    A client class for interacting with Anthropic's Chat Completion API.
    """

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=Settings.ANTHROPIC_API_KEY)

    def send_message(
        self, messages: list[Dict[str, str]], model="claude-3-5-sonnet-20240620"
    ) -> LLMMessageResponse:
        """
        Sends a message to the Anthropic Chat Completion API.
        """
        system_message, filtered_messages = self._filter_message(messages)
        logger.info(
            "ANTHROPIC_SEND_MESSAGE",
            model=model,
            filtered_messages=filtered_messages,
            system_message=system_message,
        )
        create_params = {
            "model": model,
            "max_tokens": 2000,
            "messages": filtered_messages,
        }
        if system_message:
            create_params["system"] = system_message

        try:
            response = self.client.messages.create(**create_params)
        except Exception as e:
            logger.exception("ANTHROPIC_SEND_MESSAGE_API_CALL_ERROR", error=e)
            raise e

        logger.info(
            "ANTHROPIC_SEND_MESSAGE_RESPONSE",
            model=model,
            response=response,
        )

        if not response.content:
            logger.info(
                "ANTHROPIC_SEND_MESSAGE_NO_RESPONSE",
                model=model,
                messages=messages,
                response=response,
            )
            return NoLLMResponse("No response from Anthropic")

        return LLMMessageResponse(
            content=response.content[0].text,
            role=response.role,
        )

    async def send_message_async(
        self, messages: List[Dict[str, str]], model="claude-3-5-sonnet-20240620"
    ) -> LLMMessageResponse:
        """
        Sends a message to the Anthropic Chat Completion API asynchronously.
        """
        system_message, filtered_messages = self._filter_message(messages)
        logger.info(
            "ANTHROPIC_SEND_MESSAGE",
            model=model,
            filtered_messages=filtered_messages,
            system_message=system_message,
        )
        create_params = {
            "model": model,
            "max_tokens": 2000,
            "messages": filtered_messages,
        }
        if system_message:
            create_params["system"] = system_message

        try:
            # Use asyncio.to_thread to run the synchronous API call in a separate thread
            response = await asyncio.to_thread(
                self.client.messages.create, **create_params
            )
        except Exception as e:
            logger.exception("ANTHROPIC_SEND_MESSAGE_API_CALL_ERROR", error=str(e))
            raise e
        logger.info(
            "ANTHROPIC_SEND_MESSAGE_RESPONSE",
            model=model,
            response=response,
        )

        if not response.content:
            logger.info(
                "ANTHROPIC_SEND_MESSAGE_NO_RESPONSE",
                model=model,
                messages=messages,
                response=response,
            )
            return NoLLMResponse("No response from Anthropic")

        return LLMMessageResponse(
            content=response.content[0].text,
            role=response.role,
        )

    def _filter_message(
        self, messages: List[Dict[str, str]]
    ) -> tuple[str, List[Dict[str, str]]]:
        system_message = ""
        filtered_messages = []

        for message in messages:
            if message[Role.ROLE] == Role.SYSTEM:
                system_message = message[ContentType.CONTENT]
            else:
                filtered_messages.append(message)

        return system_message, filtered_messages
