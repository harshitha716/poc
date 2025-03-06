from pydantic import BaseModel
from enum import Enum
from pantheon_v2.utils.type_utils import get_fqn
from typing import Dict, Any


class Serializer:
    @classmethod
    def get_schema_from_model_class(cls, model: type[BaseModel]):
        result = []
        for name, field in model.model_fields.items():
            if issubclass(field.annotation, Enum):
                result.append(
                    cls.get_individual_schema(
                        name,
                        get_fqn(field.annotation),
                        field.description,
                        enum=[e.value for e in field.annotation],
                    )
                )
                continue

            if isinstance(field.annotation, type) and issubclass(
                field.annotation, BaseModel
            ):
                result.append(
                    cls.get_individual_schema(
                        name,
                        get_fqn(field.annotation),
                        field.description,
                        properties=cls.get_schema_from_model_class(field.annotation),
                    )
                )
                continue

            result.append(
                cls.get_individual_schema(
                    name, get_fqn(field.annotation), field.description
                )
            )

        return result

    @classmethod
    def get_schema_from_object(cls, model: Any):
        if isinstance(model, dict):
            return cls.get_schema_from_dict(model)
        elif isinstance(model, BaseModel):
            return cls.get_schema_from_model_class(type(model))
        else:
            raise ValueError("Invalid model type")

    @classmethod
    def get_schema_from_dict(cls, model: Dict[str, Any]):
        result = []
        for key, value in model.items():
            try:
                inner_schema = cls.get_schema_from_object(value)
                current_result = cls.get_individual_schema(
                    key, get_fqn(type(value)), properties=inner_schema
                )
            except ValueError:
                enum_values = (
                    [e.value for e in value] if isinstance(value, Enum) else None
                )
                current_result = cls.get_individual_schema(
                    key, get_fqn(type(value)), enum=enum_values
                )

            result.append(current_result)

        return result

    @classmethod
    def get_individual_schema(
        cls, name, type, description="", properties=None, enum=None
    ):
        result = {"name": name, "type": type}

        if description:
            result["description"] = description
        if properties:
            result["properties"] = properties
        if enum:
            result["enum"] = enum

        return result
