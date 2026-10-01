"""Public smoke test for ordinary and positive JSONL iteration."""
import json
from io import StringIO

from boltons.jsonutils import JSONLIterator


text = "".join(json.dumps({"n": i}) + "\n" for i in range(8))
assert list(JSONLIterator(StringIO(text))) == [{"n": i} for i in range(8)]
tail = list(JSONLIterator(StringIO(text), rel_seek=0.5))
assert tail and tail[-1] == {"n": 7}
