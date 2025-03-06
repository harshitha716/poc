from pydantic import BaseModel, Field
from enum import Enum
from typing import Any, Callable

from pantheon_v2.tools.core.activity_models import Activity
from pantheon_v2.processes.core.models import Workflow, WorkflowParams
from pantheon_v2.tools.core.activity_registry import ActivityRegistry
from pantheon_v2.tools.core.activity_models import ActivityExecuteParams
from pantheon_v2.processes.core.registry import WorkflowRegistry
from pantheon_v2.processes.core.business_logic_models import BusinessLogic
from pantheon_v2.tools.common.code_executor.activities import execute_code
from pantheon_v2.tools.common.code_executor.models import ExecuteCodeParams
from pantheon_v2.tools.common.code_executor.config import CodeExecutorConfig
from pantheon_v2.core.transformers.serializer import Serializer


class ActionType(Enum):
    ACTIVITY = (0,)
    WORKFLOW = (1,)
    BUSINESS_LOGIC = (2,)


class Action(BaseModel):
    name: str
    description: str
    args: tuple
    returns: type
    long_description: str | None = None
    action_type: ActionType
    func: Callable | None = None

    @classmethod
    def from_workflow(cls, workflow: Workflow) -> "Action":
        return cls(
            name=workflow.name,
            description=workflow.description,
            args=workflow.parameters,
            returns=workflow.returns,
            long_description=workflow.func.__doc__,
            action_type=ActionType.WORKFLOW,
        )

    @classmethod
    def from_activity(cls, activity: Activity) -> "Action":
        return cls(
            name=activity.name,
            description=activity.description,
            args=activity.parameters,
            returns=activity.returns,
            long_description=activity.func.__doc__,
            action_type=ActionType.ACTIVITY,
        )

    @classmethod
    def from_business_logic(cls, business_logic: BusinessLogic) -> "Action":
        return cls(
            name=business_logic.name,
            description=business_logic.description,
            args=business_logic.parameters,
            returns=business_logic.returns,
            long_description=business_logic.func.__doc__,
            action_type=ActionType.BUSINESS_LOGIC,
            func=business_logic.func,
        )

    async def execute(self, *args, **kwargs) -> Any:
        if self.action_type == ActionType.ACTIVITY:
            return await ActivityRegistry.execute_activity(
                ActivityExecuteParams(
                    activity_name=self.name,
                    return_type=self.returns,
                    args=args,
                ),
            )
        elif self.action_type == ActionType.WORKFLOW:
            return await WorkflowRegistry.execute_workflow(
                WorkflowParams(workflow_name=self.name, args=args),
            )
        elif self.action_type == ActionType.BUSINESS_LOGIC:
            return await ActivityRegistry.execute_activity(
                activity_params=ActivityExecuteParams(
                    activity_name=execute_code,
                    args=(
                        CodeExecutorConfig(
                            timeout_seconds=30,
                        ),
                        ExecuteCodeParams(
                            function=self.func,
                            args=args,
                            kwargs=kwargs,
                        ),
                    ),
                ),
            )

    def get_model_schema(self):
        """
        Returns something like this:
        {
            "args": [
                {
                    "content": {
                        "type": "BytesIO",
                        "description": "A BytesIO object"
                    }
                },
                {
                    "id": {
                        "type": "str",
                        "description": "The id of the object"
                    },
                    "number": {
                        "type": "int",
                        "description": "The number of the object"
                    }
                }
            ],
            "returns": {
                "extracted_text": {
                    "type": "str",
                    "description": "The extracted text from the object"
                }
            }
        }
        """

        result = {
            "args": [Serializer.get_schema_from_model_class(arg) for arg in self.args],
            "returns": Serializer.get_schema_from_model_class(self.returns),
        }

        return result


class ActionFilter(BaseModel):
    name: str = Field(default="", description="The name of the action to filter by")
    labels: list[str] = Field(
        default=[], description="The labels of the action to filter by"
    )
    resticted_action_set: list[str] = Field(
        default=[], description="The action set to filter by"
    )

    def filter_actions(self, actions: list[Action]) -> list[Action]:
        filtered_actions = []
        for action in actions:
            if (
                self.resticted_action_set is not None
                and len(self.resticted_action_set) > 0
                and action.name in self.resticted_action_set
            ):
                filtered_actions.append(action)
                continue

            if self.name is not None and self.name != "" and action.name == self.name:
                filtered_actions.append(action)
                continue

        return filtered_actions
