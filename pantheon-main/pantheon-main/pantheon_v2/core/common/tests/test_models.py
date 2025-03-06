from pantheon_v2.core.common.generic_base_model import GenericBaseModel
from pydantic import BaseModel
from typing import TypeVar

T = TypeVar("T", bound=BaseModel)


class TestModel(GenericBaseModel):
    name: str


class TestModel2[T: BaseModel](GenericBaseModel):
    name: str
    test_model: T


class TestModel3[T: BaseModel](GenericBaseModel):
    name: str
    test_model: T
