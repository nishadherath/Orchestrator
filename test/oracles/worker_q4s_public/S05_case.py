"""Evaluator-only cases for zero-cache seekable memory and behaviour."""
import json
import sys
import tracemalloc

from more_itertools import seekable


def run(case):
    if case == "bounded-memory":
        stream = seekable(range(3), maxlen=0)
        tracemalloc.start()
        try:
            stream.peek()
            initial = tracemalloc.get_traced_memory()[0]
            for _ in range(10000):
                stream.peek()
                bool(stream)
            retained = tracemalloc.get_traced_memory()[0] - initial
        finally:
            tracemalloc.stop()
        return retained < 256 * 1024 and list(stream) == [0, 1, 2]
    if case == "lookahead-order":
        stream = seekable(iter([7, 8, 9]), maxlen=0)
        return (stream.peek() == 7 and next(stream) == 7
                and stream.peek() == 8 and list(stream) == [8, 9])
    if case == "empty-default":
        stream = seekable(iter(()), maxlen=0)
        return stream.peek("empty") == "empty" and not bool(stream)
    raise ValueError(case)


if __name__ == "__main__":
    print(json.dumps({"ok": run(json.load(sys.stdin)["case"])}, sort_keys=True))
