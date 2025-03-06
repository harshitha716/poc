from typing import Callable, Dict
from temporalio import workflow
from functools import wraps

from pantheon_v2.processes.core.models import Workflow, WorkflowParams
from pantheon_v2.processes.core.constants import PLATFORM_WORKFLOW_LABEL


# This class was built as a way to register workflows without coupling temporal.
class WorkflowRegistry:
    _workflows: Dict[str, Workflow] = {}

    @classmethod
    def register_workflow_defn(cls, description: str, labels: list[str]):
        def decorator(target: type):
            setattr(target, "_is_workflow_defn", True)
            workflow_name = target.__name__
            new_workflow = Workflow(
                name=workflow_name,
                description=description,
                labels=labels,
                class_type=target,
            )

            if workflow_name in cls._workflows:
                new_workflow.func = cls._workflows[workflow_name].func

            cls._workflows[workflow_name] = new_workflow
            return workflow.defn(target, name=target.__name__)

        return decorator

    @classmethod
    def register_workflow_run(cls, func: Callable) -> Callable:
        @workflow.run
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        # Get the name of the class that is wrapping func
        workflow_name = func.__name__
        if hasattr(func, "__qualname__"):
            workflow_name = func.__qualname__.split(".")[0]

        if workflow_name not in cls._workflows:
            cls._workflows[workflow_name] = Workflow(
                name=workflow_name,
                description="",
                labels=[],
                class_type=type(func),
            )

        cls._workflows[workflow_name].func = func
        return wrapper

    @classmethod
    def register_workflow_signal(cls, name: str = None):
        def decorator(func: Callable) -> Callable:
            @workflow.signal(name=name)
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)

            return wrapper

        return decorator

    @classmethod
    def get_workflow(cls, workflow_name: str) -> Workflow:
        return cls._workflows[workflow_name]

    @classmethod
    def get_available_workflows(cls, labels: list[str]) -> list[Workflow]:
        workflows = []
        if len(labels) == 0:
            return list(cls._workflows.values())

        for _workflow in cls._workflows.values():
            if PLATFORM_WORKFLOW_LABEL in _workflow.labels or any(
                label in _workflow.labels for label in labels
            ):
                workflows.append(_workflow)

        return workflows

    @classmethod
    def get_all_workflows(cls) -> list[str]:
        return list(cls._workflows.keys())

    @classmethod
    async def execute_workflow(cls, workflow_params: WorkflowParams):
        return await workflow.execute_child_workflow(
            workflow=workflow_params.workflow_name,
            *workflow_params.args,
            **workflow_params.kwargs,
        )
