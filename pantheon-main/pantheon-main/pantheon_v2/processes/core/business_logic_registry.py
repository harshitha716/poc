from typing import Callable, Dict
from functools import wraps
from pantheon_v2.processes.core.business_logic_models import (
    BusinessLogic,
)


class BusinessLogicRegistry:
    _business_logic_methods: Dict[str, BusinessLogic] = {}

    @classmethod
    def register_business_logic(cls, description: str, labels: list[str]) -> Callable:
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)

            cls._business_logic_methods[func.__name__] = BusinessLogic(
                name=func.__name__,
                description=description,
                labels=labels,
                func=wrapper,
            )
            return wrapper

        return decorator

    @classmethod
    def get_available_business_logic_list(cls) -> list[BusinessLogic]:
        return list(cls._business_logic_methods.values())

    @classmethod
    def get_business_logic_by_labels(cls, labels: list[str]) -> list[BusinessLogic]:
        return [
            business_logic
            for business_logic in cls._business_logic_methods.values()
            if any(label in business_logic.labels for label in labels)
        ]
