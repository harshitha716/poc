from pantheon_v2.core.actions.actions_hub import ActionsHub
from pantheon_v2.core.actions.models import ActionFilter
from pantheon_v2.tools.core.activity_registry import ActivityRegistry
from pantheon_v2.processes.core.registry import WorkflowRegistry
from pantheon_v2.processes.core.business_logic_registry import BusinessLogicRegistry
from pantheon_v2.processes.core.models import WorkflowParams
from unittest.mock import patch
import pytest


@ActivityRegistry.register_activity("Sample activity")
def sample_activity(name: str) -> str:
    return f"Hello {name}"


@WorkflowRegistry.register_workflow_defn(
    "Sample workflow for action hub. Do not use in production.",
    labels=["unit_test"],
)
class ActionHubSampleWorkflow:
    @WorkflowRegistry.register_workflow_run
    async def execute(self, name: str) -> str:
        return await sample_activity(name)


@BusinessLogicRegistry.register_business_logic("Sample business logic", ["unit_test"])
async def sample_business_logic(a: int, b: int) -> int:
    return a + b


def test_get_available_actions():
    actions = ActionsHub.get_available_actions(
        ActionFilter(
            labels=["unit_test"], resticted_action_set=["ActionHubSampleWorkflow"]
        )
    )
    assert len(actions) > 0


@pytest.mark.asyncio
async def test_execute_action():
    actions = ActionsHub.get_available_actions(
        ActionFilter(
            labels=["unit_test"], resticted_action_set=["ActionHubSampleWorkflow"]
        )
    )

    with patch(
        "pantheon_v2.processes.core.registry.WorkflowRegistry.execute_workflow"
    ) as mock_execute_workflow:
        mock_execute_workflow.return_value = "Hello John"
        action = actions[0]
        result = await action.execute("John")
        mock_execute_workflow.assert_called_once_with(
            WorkflowParams(workflow_name=action.name, args=("John",)),
        )
        assert result == "Hello John"


@pytest.mark.asyncio
async def test_execute_business_logic():
    actions = ActionsHub.get_available_actions(
        ActionFilter(
            labels=["unit_test"], resticted_action_set=["sample_business_logic"]
        )
    )

    assert len(actions) == 1
    action = actions[0]
    with patch(
        "pantheon_v2.tools.core.activity_registry.ActivityRegistry.execute_activity"
    ) as mock_execute_activity:
        mock_execute_activity.return_value = 3
        result = await action.execute(1, 2)
        assert result == 3


@pytest.mark.asyncio
async def test_execute_action_new():
    with patch(
        "pantheon_v2.processes.core.registry.WorkflowRegistry.execute_workflow"
    ) as mock_execute_workflow:
        mock_execute_workflow.return_value = "Hello John"
        output = await ActionsHub.execute_action(
            action_name="ActionHubSampleWorkflow",
            name="John",
        )

    assert output == "Hello John"
