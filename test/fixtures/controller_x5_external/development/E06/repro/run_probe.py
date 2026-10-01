"""Run the exit-hang case under a killable process watchdog."""

import json
from pathlib import Path
import subprocess
import sys


def run(name: str) -> dict:
    path = Path(__file__).with_name(name)
    process = subprocess.Popen(
        [sys.executable, str(path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=3.0)
    except subprocess.TimeoutExpired:
        timed_out = True
        process.kill()
        stdout, stderr = process.communicate()
    return {
        "name": name,
        "timed_out": timed_out,
        "exit_code": process.returncode,
        "stdout": stdout.strip().splitlines(),
        "stderr": stderr.strip().splitlines(),
    }


if __name__ == "__main__":
    names = ("exit_hang.py", "exit_hang_ready.py", "drain_control.py")
    print(json.dumps([run(name) for name in names], sort_keys=True))
