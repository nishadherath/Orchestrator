"""Check the response envelope without revealing the protected decision."""
import json
from pathlib import Path


value = json.loads(Path("decision.json").read_text(encoding="utf-8"))
assert set(value) == {"status", "missing_fields", "rationale"}
assert value["status"] in {"needs_input", "ready"}
assert isinstance(value["missing_fields"], list)
assert all(isinstance(field, str) and field for field in value["missing_fields"])
assert isinstance(value["rationale"], str) and value["rationale"].strip()
