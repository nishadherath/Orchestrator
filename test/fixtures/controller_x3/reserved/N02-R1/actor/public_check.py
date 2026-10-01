"""Visible smoke uses only an above-threshold value."""
import json
import subprocess
import sys

result = subprocess.run([sys.executable, "-B", "app.py"],
                        input='{"value":12,"boundary":10}\n', text=True,
                        capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout) == {"state": "warn"}
