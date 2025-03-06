from typing import List
from zamp_public_workflow_sdk.temporal.temporal_worker import Workflow
from pantheon_v2.processes.core.registry import WorkflowRegistry


def get_registered_workflows() -> List[Workflow]:
    """Returns a list of all registered workflows."""
    return [
        Workflow(
            name=workflow,
            workflow=WorkflowRegistry.get_workflow(workflow).class_type,
        )
        for workflow in WorkflowRegistry.get_all_workflows()
    ]
