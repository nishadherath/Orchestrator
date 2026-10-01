"""Keep both columns current while old readers may still run."""


def update(record, phase, value):
    return {**record, "legacy": value, "shadow": value}
