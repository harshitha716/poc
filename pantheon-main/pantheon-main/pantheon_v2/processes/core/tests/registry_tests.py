from pantheon_v2.processes.core.registry import WorkflowRegistry
import pytest
import asyncio


@WorkflowRegistry.register_workflow_defn
class TestWorkflow:
    def __init__(self):
        pass

    @WorkflowRegistry.register_workflow_run
    async def run(self):
        await asyncio.sleep(1)
        return "PING"

    @WorkflowRegistry.register_workflow_signal(name="test_signal")
    async def signal(self):
        await asyncio.sleep(1)
        return "PONG"


@pytest.mark.asyncio
async def test_workflow_registry():
    workflow = TestWorkflow()
    assert await workflow.run() == "PING"
    assert workflow.signal() == "PONG"


@pytest.mark.asyncio
async def test_workflow_registry_get_available_workflows():
    workflows = WorkflowRegistry.get_available_workflows(["netflix"])
    assert len(workflows) == 1
    assert workflows[0].name == "TestWorkflow"
