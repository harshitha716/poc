from pydantic import BaseModel, Field
from pydantic_core import PydanticOmit, core_schema
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue
from enum import Enum
from io import BytesIO


class MyGenerateJsonSchema(GenerateJsonSchema):
    def generate(self, schema, mode="validation"):
        json_schema = super().generate(schema, mode=mode)
        json_schema["title"] = "Customize title"
        json_schema["$schema"] = self.schema_dialect
        return json_schema

    def handle_invalid_for_json_schema(
        self, schema: core_schema.CoreSchema, error_info: str
    ) -> JsonSchemaValue:
        raise PydanticOmit


class MyEnum(Enum):
    A = "a"
    B = "b"


class SubModel(BaseModel):
    name: str
    age: int


class MyModel(BaseModel):
    name: str = Field(default="", description="The name of the model")
    age: int = Field(default=0, description="The age of the model")
    this_is_a_type: type[BaseModel] = Field(description="The type of the model")
    brr: SubModel = Field(
        default=SubModel(name="", age=0), description="The submodel of the model"
    )
    enum: MyEnum = Field(default=MyEnum.A, description="The enum of the model")
    bytesIO: BytesIO = Field(default=BytesIO(), description="The bytesio of the model")

    class Config:
        arbitrary_types_allowed = True
