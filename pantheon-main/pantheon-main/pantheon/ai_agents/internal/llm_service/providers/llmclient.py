from abc import ABC, abstractmethod
from typing import Dict, List
from pantheon.ai_agents.internal.llm_service.schemas.llm import LLMMessageResponse


class LLMClient(ABC):
    @abstractmethod
    def send_message(
        self, messages: List[Dict[str, str]], model: str
    ) -> LLMMessageResponse:
        pass

    @abstractmethod
    async def send_message_async(
        self, messages: List[Dict[str, str]], model: str
    ) -> LLMMessageResponse:
        pass
