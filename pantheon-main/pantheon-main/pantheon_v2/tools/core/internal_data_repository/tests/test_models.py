from pantheon_v2.tools.core.internal_data_repository.models import RelationalQueryResult

import pytest

from pydantic import BaseModel


class TestModel(BaseModel):
    name: str
    age: int


@pytest.mark.asyncio
async def test_relational_query_result():
    result = RelationalQueryResult(
        data=[TestModel(name="John Doe", age=30)], row_count=1
    )
    assert result.data[0].name == "John Doe"
    assert result.data[0].age == 30
    assert result.row_count == 1

    result_dict = result.model_dump()
    assert result_dict["data"][0]["name"] == "John Doe"
    assert result_dict["data"][0]["age"] == 30
    assert result_dict["row_count"] == 1
    assert (
        result_dict["__data_type"]
        == "pantheon_v2.tools.core.internal_data_repository.tests.test_models.TestModel"
    )


@pytest.mark.asyncio
async def test_relational_query_result_validate():
    result_dict = {
        "data": [{"name": "John Doe", "age": 30}],
        "row_count": 1,
        "__data_type": "pantheon_v2.tools.core.internal_data_repository.tests.test_models.TestModel",
    }

    result = RelationalQueryResult.model_validate(result_dict)
    assert result.data[0].name == "John Doe"
    assert result.data[0].age == 30
