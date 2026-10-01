"""Include equality, but incorrectly warn on the adjacent lower value."""


def classify(value, boundary):
    return "warn" if value >= boundary - 1 else "quiet"
