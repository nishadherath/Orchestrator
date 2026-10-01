#!/usr/bin/env python3
"""Visible happy path; no overlap, expiry or stale owner is exercised."""
import json
import subprocess
import sys

request = {"events": [
    {"op": "enqueue", "id": "m1"},
    {"op": "claim", "id": "m1", "worker": "a", "at": 0, "lease": 5},
    {"op": "ack", "id": "m1", "worker": "a", "token": 1, "at": 1},
]}
completed = subprocess.run([sys.executable, "-B", "app.py"],
                           input=json.dumps(request) + "\n", text=True,
                           capture_output=True, timeout=3)
assert completed.returncode == 0, completed.stderr
assert json.loads(completed.stdout) == {"results": [
    {"status": "enqueued"}, {"status": "claimed", "token": 1},
    {"status": "acked"}], "acked": ["m1"]}
