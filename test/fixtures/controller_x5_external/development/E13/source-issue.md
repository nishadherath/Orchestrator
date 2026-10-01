### Initial Checks

- [x] I confirm that I'm using Pydantic V2

### Description

Hello. According to the OpenAPI 3.1 spec, strict integer parsing should be relaxed.

https://swagger.io/specification/v3.1/

> Since there is no distinct JSON integer type, JSON Schema defines integers mathematically. This means that both 1 and 1.0 are [equivalent](https://datatracker.ietf.org/doc/html/draft-bhutton-json-schema-00#section-4.2.2), and are both considered to be integers.

So, to comply with the specification, we should accept values like `2.0` when the fractional part is `0` and treat them as integers even when `strict=True` is enabled.

### Example Code

```Python
import pydantic


class MyModel(pydantic.BaseModel):
    value: int = pydantic.Field(strict=True)


print(MyModel.model_validate({'value': 2.0}))
```

### Python, Pydantic & OS Version

```Text
pydantic version: 2.13.5
        pydantic-core version: 2.46.5
          pydantic-core build: profile=release pgo=false
               python version: 3.13.13 (main, Jun  2 2026, 22:27:49) [Clang 22.1.3 ]
                     platform: Linux-7.2.4-arch1-2-x86_64-with-glibc2.44
             related packages: typing_extensions-4.16.0 pydantic-extra-types-2.11.1 email-validator-2.3.0 pyright-1.1.409 pydantic-settings-2.15.0 mypy-2.3.1
                       commit: unknown
```