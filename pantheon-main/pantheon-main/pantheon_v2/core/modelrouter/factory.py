from typing import Optional
from pantheon_v2.core.modelrouter.base import BaseModelRouter, RouterOptions
from pantheon_v2.core.modelrouter.providers.litellm.router import LiteLLMRouter
from pantheon_v2.core.modelrouter.constants.constants import RouterProvider


class ModelRouterFactory:
    _instances: dict[RouterProvider, BaseModelRouter] = {}

    @classmethod
    def get_router(
        cls, provider: RouterProvider, options: Optional[RouterOptions] = None
    ) -> BaseModelRouter:
        """
        Get or create a router instance for the specified provider.
        Uses singleton pattern to ensure only one instance per provider.
        """
        if provider not in cls._instances:
            cls._instances[provider] = cls._create_router(provider, options)
        return cls._instances[provider]

    @staticmethod
    def _create_router(
        provider: RouterProvider, options: Optional[RouterOptions] = None
    ) -> BaseModelRouter:
        """Create a new router instance based on the provider."""
        match provider:
            case RouterProvider.LITELLM:
                return LiteLLMRouter(options)
            case _:
                raise ValueError(f"Unsupported router provider: {provider}")
