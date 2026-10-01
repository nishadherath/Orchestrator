"""Split a stream of byte chunks into newline-delimited frames."""


def frames(chunks: list[bytes]) -> list[bytes]:
    result = []
    for chunk in chunks:
        result.extend(chunk.split(b"\n"))
    return result
