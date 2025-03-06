from pantheon_v2.processes.core.registry import WorkflowRegistry
from pydantic import BaseModel
import asyncio


class SampleWorkflowInput(BaseModel):
    input_string: str


class SampleWorkflowOutput(BaseModel):
    output_string: str


class SampleSignal(BaseModel):
    message: str


@WorkflowRegistry.register_workflow_defn(
    "DO NOT USE IN PRODUCTION: Sample workflow", labels=["sample"]
)
class SampleWorkflow:
    def __init__(self):
        self.queue = asyncio.Queue()

    @WorkflowRegistry.register_workflow_run
    async def execute(self, input_data: SampleWorkflowInput) -> SampleWorkflowOutput:
        # Wait for something to be added to the queue
        signal = await self.queue.get()

        return SampleWorkflowOutput(
            output_string=f"You have successfully run the workflow with input {input_data.input_string} and signal {signal}"
        )

    @WorkflowRegistry.register_workflow_signal(name="sample_signal")
    async def handle_signal(self, input: SampleSignal) -> None:
        await self.queue.put(input.message)
