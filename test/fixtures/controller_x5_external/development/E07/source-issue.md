### Things to check first

- [x] I have searched the existing issues and didn't find my bug already reported there

- [x] I have checked that my bug is still present in the latest release


### AnyIO version

a995cdf 

### Python version

python>=3.10

### What happened?

I realized that we actually run async hypothesis tests on whichever backend gets picked first (when, of course, your test is parametrized to run on both backends). I was taking a look into this issue https://github.com/agronholm/anyio/issues/803, which isn't really related (I was just adding a warning in the pytest hook there)

### How can we reproduce the bug?

```python
# test_repro.py
import pytest
from hypothesis import given
from hypothesis.strategies import just
from anyio._core._eventloop import current_async_library


@pytest.mark.anyio
@given(x=just(1))
async def test_something(x):
    print("Current async lib:", current_async_library())
    assert True
```
```bash
$ pytest test_repro.py -v -s 
...
test_repro.py::test_something[asyncio] Current async lib: asyncio
PASSED
test_repro.py::test_something[trio] Current async lib: asyncio
PASSED
```
Most probably happening here:
https://github.com/agronholm/anyio/blob/a995cdfe5c16dc95093c890cac35330bac49ae33/src/anyio/pytest_plugin.py#L281-L283
One hypothesis async test object, on its second run with a different backend, doesn't get `hypothesis.inner_test` re-wrapped, and hypothesis just goes on and happily runs the test with the same (first) backend.