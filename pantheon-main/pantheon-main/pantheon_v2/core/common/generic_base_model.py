from pydantic import BaseModel
from pantheon_v2.utils.type_utils import get_fqn, get_reference_from_fqn
from typing import TypeVar
from pydantic.fields import FieldInfo


def is_base_model_type_var(field: FieldInfo) -> bool:
    if (
        field.annotation.__class__ is TypeVar
        and field.annotation.__bound__ is BaseModel
    ):
        return True

    if field._attributes_set.get("annotation") is not None:
        if (
            field._attributes_set.get("annotation").__class__ is TypeVar
            and field._attributes_set.get("annotation").__bound__ is BaseModel
        ):
            return True

    return False


class GenericBaseModel(BaseModel):
    def model_dump(self, *args, **kwargs):
        d = super().model_dump(*args, **kwargs)

        # Iterate through any field that are of issubclass(BaseModel) and dump them
        for name, field in self.model_fields.items():
            if is_base_model_type_var(field):
                attribute = getattr(self, name)
                d["__" + name + "_type"] = get_fqn(attribute.__class__)
                d[name] = attribute.model_dump(*args, **kwargs)

        return d

    @classmethod
    def model_validate(cls, obj: dict) -> "GenericBaseModel":
        pydantic_model = super().model_validate(obj)
        for name, field in cls.model_fields.items():
            if is_base_model_type_var(field):
                type_field_name = "__" + name + "_type"
                if type_field_name in obj:
                    obj_type = get_reference_from_fqn(obj.pop(type_field_name))
                    setattr(pydantic_model, name, obj_type.model_validate(obj[name]))

        return pydantic_model
