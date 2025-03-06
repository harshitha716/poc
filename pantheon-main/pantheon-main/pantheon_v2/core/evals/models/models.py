from typing import Optional, Union, Dict, Any
from pydantic import BaseModel


class TokenUsage(BaseModel):
    """Token usage information."""

    total: int
    prompt: int
    completion: int


class ProviderResponse(BaseModel):
    """Standard response format for promptfoo provider."""

    output: Optional[Union[str, Dict[str, Any]]] = None
    error: Optional[str] = None
    token_usage: Optional[TokenUsage] = None
    cost: Optional[float] = None
    cached: Optional[bool] = None
