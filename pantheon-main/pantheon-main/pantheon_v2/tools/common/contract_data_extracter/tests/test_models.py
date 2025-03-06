from pantheon_v2.tools.common.contract_data_extracter.models import (
    ContractDataExtracterOutput,
)

import pytest

from pydantic import BaseModel


class TestModel(BaseModel):
    name: str
    age: int


@pytest.mark.asyncio
async def test_contract_data_extracter_output():
    extracted_data = {
        "extracted_data": {
            "name": "John Doe",
            "age": 30,
        },
        "__extracted_data_type": "pantheon_v2.tools.common.contract_data_extracter.tests.test_models.TestModel",
    }

    output = ContractDataExtracterOutput.model_validate(extracted_data)
    assert output.extracted_data.name == "John Doe"
    assert output.extracted_data.age == 30

    output_dict = output.model_dump()
    assert output_dict["extracted_data"]["name"] == "John Doe"
    assert output_dict["extracted_data"]["age"] == 30
    assert (
        output_dict["__extracted_data_type"]
        == "pantheon_v2.tools.common.contract_data_extracter.tests.test_models.TestModel"
    )
