### Description

`BaseModel.model_construct` does not process `validation_alias`, which is expected — `model_construct` takes field names directly and skips validation. But when a field declares `validation_alias=AliasPath(...)` and the model config sets `extra='allow'`, the alias path keys are not removed from the values dict before it is stored as `_extra`. The constructed model's `model_extra`, and its serialization, then contain keys that were only ever there to satisfy the alias path.

`model_validate` with the same model and same input does not leak these keys. The two construction paths disagree.

This is a long-standing behaviour of `model_construct`, not a recent change. It reproduces on the installed release `pydantic 2.13.5` (pydantic_core 2.46.5), Python 3.12.

### Example Code

```python
from pydantic import AliasPath, BaseModel, ConfigDict, Field


class Outer(BaseModel):
    model_config = ConfigDict(extra='allow')

    x: int
    a: dict = Field(validation_alias=AliasPath('a', 'b'))


data = {'x': 1, 'a': {'b': 1}, 'c': 9}

m = Outer.model_validate(data)
print('model_validate  extra:', m.model_extra)

c = Outer.model_construct(**data)
print('model_construct extra:', c.model_extra)
print('model_construct dump :', c.model_dump())
print('model_construct dump_json:', c.model_dump_json())
```

### Observed output

```
model_validate  extra: {'c': 9}
model_construct extra: {'a': {'b': 1}, 'c': 9}
model_construct dump : {'x': 1, 'a': {'b': 1}, 'c': 9}
model_construct dump_json: {"x":1,"a":{"b":1},"c":9}
```

### Expected Behaviour

`model_construct` should not store the alias path portion of the input in `model_extra`. `model_construct` takes field names rather than aliases, so the `a` entry is not an extra key — it is the field declared with `validation_alias=AliasPath('a', 'b')`. The expectation for the output above:

```
model_construct extra: {'c': 9}
model_construct dump : {'x': 1, 'a': {'b': 1}, 'c': 9}
```

That is, `model_extra` should be `{'c': 9}` only, for parity with `model_validate`.

### Root Cause

In `BaseModel.model_construct`, the code walks the model's fields and removes each field's alias from the values dict before what remains is treated as extras. The three branches are not equivalent.

On the installed release, `pydantic 2.13.5`, in `main.py`:

- lines 344-345: the `field.alias` branch — `values.pop(field.alias)`.
- line 357: the `str` validation alias branch — `values.pop(alias)`.
- line 361: the `AliasPath` branch — `value = alias.search_dict_for_path(values)`.
- line 376: `_extra: dict[str, Any] | None = values if cls.model_config.get('extra') == 'allow' else None`.

On `main` as of `a9a0e1d1`, the same four points are at lines 361-362, 374, 378 and 393 respectively.

What differs is the shape of the operation. The first two branches `pop` from `values`, so a key consumed through `field.alias` or through a `str` `validation_alias` is gone by the time `_extra` is assigned. The `AliasPath` branch calls `search_dict_for_path`, which removes nothing: it traverses and returns. By the time line 376 (2.13.5) / 393 (`main`) assigns `_extra`, the path keys the `AliasPath` branch consumed are still in `values`, and with `extra='allow'` those entries become `model_extra`.

`search_dict_for_path` is read-only. In `aliases.py` its body is `v = d`, then a loop of `v = v[k]`, then `return v` — line 39 on the installed 2.13.5, line 38 on `main` at `a9a0e1d1`. There is no mutation and no `pop`, so the fix belongs in `model_construct`'s `AliasPath` branch rather than in the helper.

Controls, all executed against the reproduction above:

| variant | leaks? |
|---|---|
| `AliasPath('a','b')` + `extra='allow'` | yes |
| `AliasPath('a','b','c')` | yes |
| `AliasPath('a', 0)` | yes |
| `AliasPath` inside `AliasChoices` | yes |
| `validation_alias='a'` (str) — control | no |
| no `extra='allow'` | no |
| plain field-name fallback | no |

`model_validate` does not leak in any of these rows.

### Blast Radius

Narrow. Three conditions are required together:

1. the field uses `validation_alias=AliasPath(...)`, not a `str` alias;
2. the model config sets `extra='allow'`;
3. the model is built with `model_construct`, not `model_validate`.

`model_validate` is unaffected in every configuration tested.

The caller's input dict is **not** mutated — neither for `model_construct(**src)` nor for `model_construct(mapping)`. `search_dict_for_path` does not write to the dict it is given, and nothing else in the path removes keys from the caller's object. The stray key is confined to the constructed model: it appears in `model_extra` and in `model_dump` / `model_dump_json`, and does not leak back out to the caller's data.

One further edge: if the field name collides with the path root, the field is also dropped from the dump.

On duplicate search: I did not find an existing report for this. `#8266` is closed and different — `model_construct` not storing non-allowed extras, no `AliasPath`, no `extra='allow'`. `#11046` is closed and different — an `AliasChoices` `KeyError` in `model_construct`, a different failure mode. `#12884` is the nearest open issue, but it is an alias/name collision during serialization and names neither `AliasPath` nor `model_construct`; mentioning it as a possible cross-reference only, not as the same issue.

### Python/Pydantic/OS Version

- pydantic 2.13.5 (installed release)
- pydantic_core 2.46.5
- Python 3.12

The same source locations are present on `main` at `a9a0e1d1`, at the line numbers given in Root Cause.

### AI assistance disclosure

AI assistance was used to prepare this report, including the reproduction script and the control variants. Every output quoted above was produced by executing the code, and the line numbers were read from the installed 2.13.5 sources and from `main` at `a9a0e1d1`.