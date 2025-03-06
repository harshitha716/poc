from pydantic import BaseModel, Field
from typing import Any, Optional
from temporalio.common import RetryPolicy


class WorkflowParams(BaseModel):
    workflow: str = Field(..., description="Name of the workflow to execute")
    arg: Any = Field(..., description="Workflow input argument")
    task_queue: str = Field(..., description="Task queue name")
    id: str = Field(..., description="Workflow ID")
    retry_policy: Optional[RetryPolicy] = Field(
        None, description="Retry policy for the workflow"
    )


class WorkflowResponse(BaseModel):
    workflow_id: str = Field(..., description="Workflow ID")
    run_id: str = Field(..., description="Run ID")
    result: Any = Field(..., description="Workflow result")
