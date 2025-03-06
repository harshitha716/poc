from pantheon_v2.core.transformers.serializer import Serializer
from pantheon_v2.core.transformers.tests.test_models import SubModel, MyModel
from io import BytesIO


def test_serializer_dict():
    extracted_value = Serializer.get_schema_from_object(
        {
            "a": 1,
            "b": BytesIO("alskejfsl".encode()),
            "c": {"d": SubModel(name="", age=0), "e": 4},
        }
    )

    assert extracted_value == [
        {"name": "a", "type": "int"},
        {"name": "b", "type": "_io.BytesIO"},
        {
            "name": "c",
            "type": "dict",
            "properties": [
                {
                    "name": "d",
                    "type": "pantheon_v2.core.transformers.tests.test_models.SubModel",
                    "properties": [
                        {"name": "name", "type": "str"},
                        {"name": "age", "type": "int"},
                    ],
                },
                {"name": "e", "type": "int"},
            ],
        },
    ]


def test_serializer_pydantic_model_type():
    extracted_value = Serializer.get_schema_from_model_class(MyModel)

    assert extracted_value == [
        {"name": "name", "type": "str", "description": "The name of the model"},
        {"name": "age", "type": "int", "description": "The age of the model"},
        {
            "name": "this_is_a_type",
            "type": "type",
            "description": "The type of the model",
        },
        {
            "name": "brr",
            "type": "pantheon_v2.core.transformers.tests.test_models.SubModel",
            "description": "The submodel of the model",
            "properties": [
                {"name": "name", "type": "str"},
                {"name": "age", "type": "int"},
            ],
        },
        {
            "name": "enum",
            "type": "pantheon_v2.core.transformers.tests.test_models.MyEnum",
            "enum": ["a", "b"],
            "description": "The enum of the model",
        },
        {
            "name": "bytesIO",
            "type": "_io.BytesIO",
            "description": "The bytesio of the model",
        },
    ]
