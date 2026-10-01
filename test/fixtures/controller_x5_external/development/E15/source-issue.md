### Initial Checks

- [x] I confirm that I'm using Pydantic V2

### Description

Using a `None` type alias as a member of a discriminated union fails during schema construction with `TypeError: The core schema type 'none' is not a valid discriminated union variant.`. The alias generates a `'none'` core schema reached through a `'definition-ref'`, and while `_handle_choice()` handles `'none'` choices (by wrapping the tagged union in a `'nullable'` schema), `_infer_discriminator_values_for_choice()` (which is what resolves `'definition-ref'` choices) doesn't.

Once https://github.com/pydantic/pydantic/pull/13779 lands, the same applies to a type alias to the `MISSING` sentinel (a schema-less `'missing-sentinel'` schema reached through a `'definition-ref'`, see [this review comment](https://github.com/pydantic/pydantic/pull/13779#discussion_r3965416688)).

### Example Code

```python
from typing import Annotated, Literal

from typing_extensions import TypeAliasType

from pydantic import BaseModel, Field


class Cat(BaseModel):
    kind: Literal['cat']


class Dog(BaseModel):
    kind: Literal['dog']


NoneAlias = TypeAliasType('NoneAlias', None)


class Model(BaseModel):
    pet: Annotated[NoneAlias | Cat | Dog, Field(discriminator='kind')] = None
#> TypeError: The core schema type 'none' is not a valid discriminated union variant.
```
