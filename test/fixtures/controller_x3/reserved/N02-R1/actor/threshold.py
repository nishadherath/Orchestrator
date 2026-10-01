"""Local display warning threshold."""


def classify(value, boundary):
    return "warn" if value > boundary else "quiet"
