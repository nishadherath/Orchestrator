## Initial Checks

- [x] I confirm that I'm using Pydantic V2

## Description

This is kin of #11700 (private attributes in multiple inheritance don't respect the MRO). That issue's example shows public fields resolving correctly when both bases declare the field. This report covers the shape that still diverges from the MRO: a base that *merely inherits* an attribute shadows a later base's override.

The same shape with plain Python classes resolves per the MRO, for both attribute kinds, in both base orders:

```python
class Base:
    f = "base"
    _knob = "base"

class Override(Base):
    f = "override"
    _knob = "override"

class Plain(Base):
    pass

class Swapped(Plain, Override):
    pass

class Composed(Override, Plain):
    pass

print(Swapped().f, Swapped()._knob)    # override override
print(Composed().f, Composed()._knob)  # override override
```

## Example Code

```python
from pydantic import BaseModel

class Base(BaseModel):
    f: str = "base"
    _knob: str = "base"

class Override(Base):
    f: str = "override"
    _knob: str = "override"

class Plain(Base):
    pass

class Swapped(Plain, Override):
    pass

class Composed(Override, Plain):
    pass

print(Swapped.mro())  # [Swapped, Plain, Override, Base, BaseModel, object]
print(Swapped().f, Swapped()._knob)    # base override
print(Composed().f, Composed()._knob)  # override base
```

`Plain` never declares `f` or `_knob`; it only carries inherited copies in its flattened `__pydantic_fields__` and `__private_attributes__`.

| base order | field | private attr |
|---|---|---|
| `(Plain, Override)` | `"base"` ❌ | `"override"` ✅ |
| `(Override, Plain)` | `"override"` ✅ | `"base"` ❌ |

Native Python resolves `override override` for both attribute kinds in both orders. No ordering of the same two pydantic bases resolves both correctly. Each merge picks a winner from the declared bases in a fixed direction: fields take the first declared base whose flattened `__pydantic_fields__` contains the name (inherited copies included), private attributes take the last declared base. The two directions are opposite, so each rule is MRO-correct only in the shape where the other breaks. #11700's example happened to use the both-declare shape, where fields resolve correctly, which is likely why the field side went unnoticed.

## Cause as I read it

Inherited fields are merged from base snapshots in declared order, where the first declared base whose snapshot contains the name wins, inherited copies included. A base that merely inherits the field therefore occupies the winning slot over a later base's override. Merging in MRO order would fix this and #11700 together.

## Python, Pydantic & OS Version

```
pydantic version: 2.13.4
python version: 3.14.7
platform: macOS-26.5.2
```
