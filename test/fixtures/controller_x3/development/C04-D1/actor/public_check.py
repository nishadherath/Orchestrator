#!/usr/bin/env python3
"""Visible same-tenant cache hit; cross-tenant reuse is not exercised."""
import json
import subprocess
import sys

request = {"events": [
    {"op": "put", "tenant": "a", "feature": "beta", "value": True},
    {"op": "get", "tenant": "a", "feature": "beta"},
]}
completed = subprocess.run([sys.executable, "-B", "app.py"],
                           input=json.dumps(request) + "\n", text=True,
                           capture_output=True, timeout=3)
assert completed.returncode == 0, completed.stderr
assert json.loads(completed.stdout) == {"results": [
    {"status": "stored"}, {"status": "hit", "value": True}]}
