"""Public smoke test for existing plain and single-slash behaviour."""
from pathlib import Path
from tempfile import TemporaryDirectory
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from dotenv import dotenv_values, set_key
from dotenv.parser import parse_stream
from io import StringIO


with TemporaryDirectory() as directory:
    path = Path(directory) / ".env"
    path.write_text("KEEP=ok\n", encoding="utf-8")
    for value in ("plain", "C:" + chr(92) + "Users"):
        set_key(str(path), "VALUE", value)
        parsed = dotenv_values(path)
        assert parsed.get("VALUE") == value
        assert parsed.get("KEEP") == "ok"

rows = list(parse_stream(StringIO("first='plain'\nsecond='ok'")))
assert [row.key for row in rows] == ["first", "second"]
assert [row.value for row in rows] == ["plain", "ok"]
assert not any(row.error for row in rows)
