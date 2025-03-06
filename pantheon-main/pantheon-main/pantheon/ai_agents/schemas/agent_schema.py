from pydantic import BaseModel
from typing import List


class AgentQueryResponse(BaseModel):
    status: str
    action: str
    content: str
    explanation: str


class Param(BaseModel):
    name: str
    value: str


class Action(BaseModel):
    name: str
    params: List[Param]
    sequence_no: int


class TransformationsActionsResponse(BaseModel):
    status: str
    actions: List[Action]
