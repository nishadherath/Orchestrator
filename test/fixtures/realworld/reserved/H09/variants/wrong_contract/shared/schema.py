class Result:
    def __init__(self, value, warnings=()): self.data=value; self.errors=list(warnings)
def make_result(value, warnings=()): return Result(value, warnings)
