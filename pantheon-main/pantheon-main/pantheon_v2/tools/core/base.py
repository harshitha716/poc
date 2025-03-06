from abc import ABC, abstractmethod


class BaseTool(ABC):
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the tool"""
        pass
