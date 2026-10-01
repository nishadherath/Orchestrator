"""Request-scoped UI heading and footer formatting."""


def heading(text, parts=[]):
    parts.append(text)
    return " > ".join(parts)


def footer(text, parts=[]):
    parts.append(text)
    return " / ".join(parts)
