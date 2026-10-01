### Initial Checks

- [x] I confirm that I'm using Pydantic V2

### Description

When a model has a `model_validator(mode='wrap')` and validation fails inside a nested validator, the `handler` object (`ValidatorCallable`) stays alive as long as the resulting `ValidationError` is alive: the `ValueError` stored in the error `ctx` keeps its traceback, the traceback keeps the field-validator frame, its `f_back` is the wrap-validator frame, and that frame still holds the local `handler`.

If a garbage collection runs while the handler is alive, CPython's GC visits every Python object owned by the model's validator tree **twice**:

- `SchemaValidator.__traverse__` → `FunctionWrapValidator { validator, func, config }` → the validator tree (`src/validators/function.rs`);
- `ValidatorCallable.__traverse__` → `InternalValidator { validator, data, context, self_instance }` (`src/validators/generator.rs`, `impl_py_gc_traverse!(InternalValidator { validator, data, context, self_instance })`), where `validator` is an `Arc` clone of the **same** tree.

Each `Py<PyAny>` inside the tree (bound validator methods, model classes, configs) is owned once but visited twice, so `subtract_refs` drives `gc_refs` below zero. On a debug build of CPython this is an immediate abort:

```
Python/gc.c:94: gc_decref: Assertion "gc_get_refs(g) > 0" failed: refcount is too small
object type name: ModelMetaclass
object repr     : <class '__main__.A'>
Fatal Python error: _PyObject_AssertFailed: _PyObject_AssertFailed
```

On a release build the miscounted objects can be treated as unreachable and cleared while still in use, which shows up as random SIGSEGV/SIGABRT later in the process. We hit this in production and CI with django-ninja, whose `Schema` base class installs a `model_validator(mode='wrap')` on every model, so every failed request-body validation triggers it (downstream report: vitalik/django-ninja#1773, workaround PR vitalik/django-ninja#1774).

The same pattern exists for `ValidatorIterator` (generator validation), which also owns an `InternalValidator` with an `Arc` clone of the item validator tree.

Removing the extra reference in the wrap validator (`try: return handler(values) finally: del handler`) makes the reproducer pass, which confirms the mechanism. A proper fix is probably to stop traversing `InternalValidator.validator` (the tree is owned and traversed by the `SchemaValidator`), similar to what pydantic/pydantic-core#1125 did for `DefinitionRefValidator`, or to hold a `Py<SchemaValidator>` inside `InternalValidator` so that the ownership is expressed as a real Python reference.

Reproduced with pydantic 2.12.5 / pydantic-core 2.41.5 and with pydantic 2.13.5 / pydantic-core 2.46.5, on macOS arm64 and Linux x86_64. Without the `model_validator(mode='wrap')`, or with `del handler` in a `finally` block inside `_run`, the script below prints `ok`.

### Example Code

Run with a debug build of CPython (`--with-pydebug`, e.g. `uv python install 3.13+debug`); `python -X dev` is not enough because the assertion lives in `gc.c`.

```python
import gc
from datetime import datetime

from pydantic import BaseModel, ValidationError, field_validator, model_validator


class A(BaseModel):
    created_at: datetime

    @field_validator('created_at')
    @classmethod
    def check(cls, v):
        raise ValueError('bad')

    @model_validator(mode='wrap')
    @classmethod
    def _run(cls, values, handler, info):
        return handler(values)


kept = []
for _ in range(5):
    try:
        A(created_at='2020-01-01T00:00:00')
    except ValidationError as e:
        kept.append(e)  # keeps the ValueError and its traceback alive
    gc.collect()  # aborts on the first iteration
print('ok')
```

A variant that does not need a debug build: keep the `ValidationError`, call `gc.collect()` and look for live `ValidatorCallable` objects in `gc.get_objects()` — one stays alive for as long as the error does.

### Python, Pydantic & OS Version

```
             pydantic version: 2.12.5
        pydantic-core version: 2.41.5
          pydantic-core build: profile=release pgo=false
               python version: 3.13.9 (main, Oct 31 2025, 23:03:53) [Clang 21.1.4 ]
                     platform: macOS-26.3.1-arm64-arm-64bit-Mach-O
             related packages: typing_extensions-4.16.0
                       commit: unknown
```

CPython 3.13.9 debug build (`uv python install 3.13+debug`), pydantic-core built from the sdist for the debug ABI. Also reproduced on Linux x86_64 and with pydantic-core built from source with pyo3 0.26.0.
