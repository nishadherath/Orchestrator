# Bounded lookahead for zero-cache seekable

Repeated `peek()` and truth checks on a `seekable` iterator with `maxlen=0`
should retain bounded memory while leaving the next element available.
Keep ordinary iteration and empty-iterator behaviour intact. The requested
change is confined to `more_itertools/more.py`; `recipes.py` is available
only if needed for a narrow supporting edit. There is no cross-component
contract in this task.

Run `python3 -B public_check.py`. Source edits are limited to
`more_itertools/more.py` and `more_itertools/recipes.py`.
Do not edit the issue, public check, acceptance contract or licence.
