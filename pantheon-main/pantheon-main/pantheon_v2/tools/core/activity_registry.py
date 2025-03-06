from functools import wraps
from typing import Dict, Callable

from temporalio import activity, workflow
import structlog

from pantheon_v2.tools.core.activity_models import Activity, ActivityExecuteParams

logger = structlog.get_logger(__name__)


class ActivityRegistry:
    _activities: Dict[str, Activity] = {}

    @classmethod
    def register_activity(cls, description: str):
        """
        Register a activity decorator with optional description
        """

        def decorator(func: Callable) -> Callable:
            activity_name = func.__name__
            if activity_name in cls._activities:
                raise ValueError(
                    f"Activity '{activity_name}' already registered. Please use a unique name."
                )

            @activity.defn(name=activity_name)
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await func(*args, **kwargs)

            new_activity = Activity(
                name=func.__name__, description=description, func=async_wrapper
            )

            assert new_activity.parameters is not None
            assert new_activity.returns is not None

            cls._activities[func.__name__] = new_activity
            wrapper = async_wrapper
            wrapper._is_activity = True
            wrapper._description = description
            return wrapper

        return decorator

    @classmethod
    def get_activity_details(cls, activity_name: str) -> Activity:
        return cls._activities[activity_name]

    @classmethod
    def get_available_activities(cls) -> list[Activity]:
        return list(cls._activities.values())

    @classmethod
    async def execute_activity(cls, activity_params: ActivityExecuteParams):
        return await workflow.execute_activity(
            activity=activity_params.activity_name,
            result_type=activity_params.return_type,
            args=activity_params.args,
        )
