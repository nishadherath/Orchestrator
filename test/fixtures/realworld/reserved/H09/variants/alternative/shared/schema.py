from typing import NamedTuple
class Result(NamedTuple):
    value: object
    warnings: tuple[str, ...] = ()
def make_result(value, warnings=()): return Result(value, tuple(warnings))
