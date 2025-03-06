from pydantic import BaseModel
from typing import List


class Param(BaseModel):
    name: str
    value: str


class Action(BaseModel):
    name: str
    params: List[Param]
    sequence_no: int


class HermTransformationsActionsResponse(BaseModel):
    actions: List[Action]
    status: str
