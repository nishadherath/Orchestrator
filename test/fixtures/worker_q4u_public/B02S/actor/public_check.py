"""Direct public checks for both bounded relative-seek paths."""
import json
from io import StringIO

from boltons.jsonutils import JSONLIterator


class BoundedRead:
    def __init__(self, source):
        self.source = source
        self.reads = 0

    def read(self, size=-1):
        self.reads += 1
        if self.reads > 12:
            raise AssertionError("relative seek did not terminate")
        return self.source.read(size)

    def __iter__(self):
        return iter(self.source)

    def __getattr__(self, name):
        return getattr(self.source, name)


incomplete = '{"n": 0}\n{"n": 1}\n{"n": 2}\n{"n": 3}'
assert list(JSONLIterator(BoundedRead(StringIO(incomplete)), rel_seek=0.95)) == []
text = "".join(json.dumps({"n": i}) + "\n" for i in range(10))
tail = list(JSONLIterator(BoundedRead(StringIO(text)), rel_seek=-0.25))
positive = list(JSONLIterator(BoundedRead(StringIO(text)), rel_seek=0.75))
assert tail and tail == positive
