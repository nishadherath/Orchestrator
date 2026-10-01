"""Local direct reproduction of Pydantic issue 13754."""

import json

from pydantic import BaseModel, ConfigDict, Field, computed_field


class Model(BaseModel):
    my_field: str = Field(serialization_alias="myAlias")

    @computed_field(alias="computedAlias")
    @property
    def computed(self) -> str:
        return "v"


class AliasModel(Model):
    model_config = ConfigDict(serialize_by_alias=True)


def observe(model: type[BaseModel]) -> dict:
    instance = model(my_field="foo")
    return {
        "dump_keys": list(instance.model_dump()),
        "schema_keys": list(model.model_json_schema(mode="serialization")["properties"]),
        "schema_by_alias_false_keys": list(
            model.model_json_schema(mode="serialization", by_alias=False)["properties"]
        ),
        "schema_by_alias_true_keys": list(
            model.model_json_schema(mode="serialization", by_alias=True)["properties"]
        ),
    }


if __name__ == "__main__":
    print(json.dumps({"default": observe(Model), "alias_true": observe(AliasModel)}, sort_keys=True))
