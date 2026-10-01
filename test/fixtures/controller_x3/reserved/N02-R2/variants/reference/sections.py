"""Each UI section call gets fresh text parts."""


def heading(text, parts=None):
    current = [] if parts is None else list(parts)
    current.append(text)
    return " > ".join(current)


def footer(text, parts=None):
    current = [] if parts is None else list(parts)
    current.append(text)
    return " / ".join(current)
