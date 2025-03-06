from pydantic import BaseModel, Field
from typing import Any, Dict, Optional


class ExecuteCodeParams(BaseModel):
    function: Any = Field(..., description="Callable function to execute")
    args: tuple = Field(
        default=(), description="Positional arguments to pass to the function"
    )
    kwargs: Dict[str, Any] = Field(
        default_factory=dict, description="Keyword arguments to pass to the function"
    )


class ExecutionResult(BaseModel):
    success: bool = Field(..., description="Whether the execution was successful")
    result: Optional[Any] = Field(
        None, description="Result of the function execution if successful"
    )
    error: Optional[str] = Field(None, description="Error message if execution failed")
    execution_time: float = Field(
        ..., description="Time taken for execution in seconds"
    )
