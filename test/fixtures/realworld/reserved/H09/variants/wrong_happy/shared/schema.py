from dataclasses import dataclass
@dataclass(frozen=True)
class Result: value: object; warnings: tuple = ()
def make_result(value, warnings=()): return Result(value, tuple(warnings))
