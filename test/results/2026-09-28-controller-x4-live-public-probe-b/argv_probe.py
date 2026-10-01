"""Provider-free check of JSON argv transport through Windows wsl.exe."""
import json
import base64
import subprocess

schema = json.dumps({"type": "object", "properties": {"a": {"type": "string"}}},
                    separators=(",", ":"))
for label, value in (
    ("raw", schema),
    ("slash-quote", schema.replace('"', '\\"')),
    ("double-slash-quote", schema.replace('"', '\\\\"')),
    ("base64", base64.urlsafe_b64encode(schema.encode()).decode()),
):
    proc = subprocess.run(
        ["wsl.exe", "-d", "kali-linux", "-u", "wsl", "--",
         "/usr/bin/printf", "%s", value],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=20)
    print(label, proc.returncode, repr(proc.stdout), repr(proc.stderr))
