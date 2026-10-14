"""Review xperf CSV callback pairs for one PID; never elevate or start tracing."""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


def analyse(path: Path, pid: int) -> dict:
    pending = {}
    modules = {}
    slow = []
    init_count = 0
    pid_pattern = re.compile(r"\(\s*" + str(pid) + r"\s*\)$")
    events = {"MiniFilterPreOpInit", "MiniFilterPostOpInit",
              "MiniFilterPreOpComp", "MiniFilterPostOpComp"}
    with path.open(encoding="utf-8-sig", errors="strict", newline="") as source:
        for row in csv.reader(source, skipinitialspace=True):
            row = [value.strip() for value in row]
            if len(row) < 12 or row[0] not in events:
                continue
            try:
                stamp = int(row[1])
            except ValueError:
                continue  # xperf also exports its column headers
            phase = row[0].removesuffix("Init").removesuffix("Comp")
            key = (phase, row[5], row[6], row[7], row[8], row[-1])
            if row[0].endswith("Init"):
                # Another request can reuse a pointer. Never match its completion
                # to an older request from the target process.
                pending.pop(key, None)
                if pid_pattern.search(row[2]):
                    pending[key] = (stamp, row[3])
                    init_count += 1
                continue
            initial = pending.pop(key, None)
            if initial is None or stamp < initial[0]:
                continue
            elapsed = stamp - initial[0]
            # Initial Time in a completion row is raw QPC, not exported us.
            # Subtract only the two paired exported TimeStamp values.
            stats = modules.setdefault(row[7], {"matched_callbacks": 0,
                                                "sum_callback_elapsed_us": 0,
                                                "max_callback_elapsed_us": 0})
            stats["matched_callbacks"] += 1
            stats["sum_callback_elapsed_us"] += elapsed
            stats["max_callback_elapsed_us"] = max(stats["max_callback_elapsed_us"], elapsed)
            if elapsed >= 10000:
                slow.append({"module": row[7], "elapsed_us": elapsed,
                             "initial_us": initial[0], "completion_us": stamp,
                             "pid": pid, "tid": initial[1], "operation": row[6],
                             "callback_phase": phase})
    return {"pid": pid, "own_init_events": init_count,
            "matched_callback_count": sum(value["matched_callbacks"] for value in modules.values()),
            "unclosed_callbacks": len(pending), "modules": modules,
            "slow_matched_callbacks": sorted(slow, key=lambda value: value["elapsed_us"], reverse=True),
            "paths_and_request_pointers_omitted": True,
            "unique_timeout_cause_proven": False,
            "limits": "Callback elapsed includes scheduling waits. Check trace loss, circular overwrite, module identity and workload overlap separately. Totals cover matched retained events only."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True, help="Local xperf dumper export or reviewed callback subset")
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.pid <= 0:
        parser.error("PID must be positive")
    try:
        data = analyse(args.csv, args.pid)
        text = json.dumps(data, indent=2) + "\n"
        if args.output:
            args.output.write_bytes(text.encode())
        print(text, end="")
        return 0
    except (OSError, UnicodeError, csv.Error) as exc:
        parser.exit(1, f"Cannot review CSV ({type(exc).__name__}); preserve the input and inspect its format/permissions.\n")


if __name__ == "__main__":
    raise SystemExit(main())
