import io
import base64
from typing import Annotated, List
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, core_schema
from pydantic import GetJsonSchemaHandler
from typing import Any, Type, Callable


class BytesIOConverter:
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Type[io.BytesIO],
        _handler: Callable[[Any], CoreSchema],
    ) -> CoreSchema:
        def validate_from_str(value: str) -> io.BytesIO:
            return io.BytesIO(base64.b64decode(value))

        def validate_from_bytes(value: bytes) -> io.BytesIO:
            return io.BytesIO(value)

        def validate_from_array(value: List[List[int]]) -> io.BytesIO:
            # New validator for array format
            flat_bytes = bytes([byte for subarray in value for byte in subarray])
            return io.BytesIO(flat_bytes)

        def serialize_bytesio(value: io.BytesIO) -> str:
            return base64.b64encode(value.getvalue()).decode()

        from_str_schema = core_schema.chain_schema(
            [
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(validate_from_str),
            ]
        )

        from_bytes_schema = core_schema.chain_schema(
            [
                core_schema.bytes_schema(),
                core_schema.no_info_plain_validator_function(validate_from_bytes),
            ]
        )

        from_array_schema = core_schema.chain_schema(
            [
                core_schema.list_schema(
                    core_schema.list_schema(core_schema.int_schema())
                ),
                core_schema.no_info_plain_validator_function(validate_from_array),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=from_str_schema,
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(io.BytesIO),
                    from_bytes_schema,
                    from_str_schema,
                    from_array_schema,  # Added array schema
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                serialize_bytesio,
                return_schema=core_schema.str_schema(),
                when_used="json",
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        _core_schema: CoreSchema,
        _handler: GetJsonSchemaHandler,
    ) -> JsonSchemaValue:
        return {"type": "string", "format": "base64"}


SerializableBytesIO = Annotated[io.BytesIO, BytesIOConverter]
