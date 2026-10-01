### Initial Checks

- [X] I confirm that I'm using Pydantic V2

### Description

With `serialize_by_alias=False` (the default since v2.11) `model_dump()` emits the field name, but `model_json_schema(mode='serialization')` still keys the properties by the `serialization_alias`, so the serialization schema names keys the model never emits

same happens with `alias=` and with computed field aliases. consumers generating client schemas from the serialization mode get keys that never appear in the actual output, and the schema contradicts `model_dump()` on the exact same model

with `serialize_by_alias=True` both agree (alias everywhere), so the inconsistency only shows on the default config

i found this while following up on #13717 (validation side, `validate_by_alias=False`), which fixed the same mismatch for the validation schema, and its test comment noted serialization was left alone. #8379 tracks the general alias consistency work

### Example Code

```python
from pydantic import BaseModel, Field, computed_field

class Model(BaseModel):
    my_field: str = Field(serialization_alias='myAlias')

    @computed_field(alias='computedAlias')
    @property
    def computed(self) -> str:
        return 'v'

m = Model(my_field='foo')

print(list(m.model_dump().keys()))
#> ['my_field', 'computed']

print(list(Model.model_json_schema(mode='serialization')['properties']))
#> ['myAlias', 'computedAlias']   <-- never emitted by model_dump()
```

### Python, Pydantic & OS Version

```text
             pydantic version: 2.14.0b1
        pydantic-core version: 2.48.0
          pydantic-core build: profile=debug pgo=false
               python version: 3.11.15 (main, May 10 2026, 19:28:18) [Clang 22.1.3 ]
                     platform: Linux-7.0.0-28-generic-x86_64-with-glibc2.39
             related packages: typing_extensions-4.15.0
```

the mismatch reproduces on a clean checkout of pydantic main (no patch), checked at 27f473c