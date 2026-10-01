"""Direct public checks for both requested backslash contracts."""
import sys
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from dotenv import dotenv_values, set_key
from dotenv.parser import parse_stream


slash = chr(92)
with TemporaryDirectory() as directory:
    path = Path(directory) / ".env"
    path.write_text("KEEP=ok\n", encoding="utf-8")
    value = "prefix" + slash * 2 + "suffix"
    set_key(str(path), "VALUE", value)
    parsed = dotenv_values(path)
    assert parsed.get("VALUE") == value
    assert parsed.get("KEEP") == "ok"

for quote in ("'", '"'):
    raw = "key=" + quote + "value" + slash * 2 + quote + "\nnext=" + quote + "present" + quote
    rows = list(parse_stream(StringIO(raw)))
    assert [row.key for row in rows] == ["key", "next"]
    assert [row.value for row in rows] == ["value" + slash, "present"]
    assert [row.original.line for row in rows] == [1, 2]
    assert not any(row.error for row in rows)
