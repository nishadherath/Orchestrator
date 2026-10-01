"""Public smoke checks for allocation, including a stable remainder tie."""
from allocation import allocate


assert allocate(10, [3, 2, 1]) == [5, 3, 2]
assert allocate(2, [1, 1, 1]) == [1, 1, 0]
assert allocate(0, [1, 2]) == [0, 0]
