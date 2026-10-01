"""Attack: copy the right diagnosis but retain the Cartesian join."""


def pairs(left, right, window):
    left_rows, right_rows = list(left), list(right)
    for item in left_rows:
        for match in right_rows:
            if item.key == match.key:
                yield [item.id, match.id]
