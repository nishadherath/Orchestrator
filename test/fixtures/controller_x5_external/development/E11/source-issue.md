### Initial Checks

- [x] I confirm that I'm using Pydantic V2

### Description

Serialization with `SerializeAsAny` fails when the runtime class of the value is a deferred model.
A deferred model is a model with `defer_build=True` that pydantic did not build yet.
The call raises this error:

```
PydanticSerializationError: Error serializing to JSON: TypeError: 'MockValSer' object is not an instance of 'SchemaSerializer'
```

I expect pydantic to build the deferred model at first use, and then serialize the value.

### Cause

The cause is in pydantic-core, in `src/serializers/infer.rs`.
The function `serialize_pydantic_serializable` reads the attribute `__pydantic_serializer__` from the value.
On a deferred model, this attribute holds a `MockValSer` object, not a `SchemaSerializer` object.
The code downcasts the object to `SchemaSerializer`.
The downcast fails, and the error goes to the caller.

`MockValSer` has a lazy rebuild hook in `__getattr__`.
A Python method call starts this hook.
A Rust downcast does not start this hook.
As a result, the same deferred instance serializes correctly through a direct `model_dump_json()`, but fails through `SerializeAsAny`.
The example code below shows this asymmetry.

### Impact

This failure occurred for us in production.
A worker process serialized instances of model classes that it never validated in that process.
Each `model_dump_json()` call on the parent model failed.

### Versions tested

The failure occurs on all versions that we tested:

- pydantic 2.12.5 / pydantic-core 2.41.5
- pydantic 2.13.4 / pydantic-core 2.46.4
- pydantic 2.14.0b1 / pydantic-core 2.48.0

### Related issues

- #7713 tracks `MockValSer` errors in general.
- #12282 reported this failure and was closed as a duplicate.

### Proposed fix

I have a fix with tests ready on a fork.
The fix changes `get_pydantic_serializer` in `infer.rs`:

1. The function downcasts the attribute value to `SchemaSerializer` as before.
2. If the downcast fails, the function calls the `rebuild()` method of the mock object.
3. The function then uses the serializer that `rebuild()` returns.
4. An object without a `rebuild()` method keeps the current downcast error.

`serialize_pydantic_serializable` and `PolymorphismTrampoline` use the same code path, so one change repairs both.
All pydantic and pydantic-core test suites pass with the fix.
Please assign this issue to me, and I will open the pull request.


### Example Code

```Python
from typing import Optional

from pydantic import BaseModel, ConfigDict, SerializeAsAny


class Child(BaseModel):
    model_config = ConfigDict(defer_build=True)
    x: int = 1


class Sub(Child):
    y: int = 2


class Parent(BaseModel):
    content: Optional[SerializeAsAny[Child]] = None


# model_construct() does not validate, so pydantic does not build Sub.
# This is equal to a process that serializes a class that it never validated.
sub = Sub.model_construct(x=1, y=2)
parent = Parent.model_construct(content=sub)
assert Sub.__pydantic_complete__ is False

# 1) The SerializeAsAny path fails on the deferred model.
try:
    parent.model_dump_json()
except Exception as e:
    print(f"{type(e).__name__}: {e}")
    # PydanticSerializationError: Error serializing to JSON: TypeError:
    # 'MockValSer' object is not an instance of 'SchemaSerializer'

# 2) The direct Python path rebuilds the same deferred model and succeeds.
print(sub.model_dump_json())  # {"x":1,"y":2}
assert Sub.__pydantic_complete__ is True

# 3) After the rebuild, the SerializeAsAny path also succeeds.
print(parent.model_dump_json())  # {"content":{"x":1,"y":2}}
```

### Python, Pydantic & OS Version

```Text
pydantic version: 2.14.0b1
        pydantic-core version: 2.48.0
          pydantic-core build: profile=release pgo=false
               python version: 3.11.15 (main, Mar 25 2026, 02:58:47) [Clang 22.1.1 ]
                     platform: macOS-26.5.2-arm64-arm-64bit
             related packages: typing_extensions-4.16.0
                       commit: unknown

The same example also fails on these versions:
- pydantic 2.13.4 / pydantic-core 2.46.4 (latest stable)
- pydantic 2.12.5 / pydantic-core 2.41.5
```