"""Read Linux wait states for one explicitly selected process and descendants."""
import argparse
import json
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--seconds", type=float, default=60)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not (0 < args.seconds <= 300) or args.pid <= 1:
        parser.error("Select an owned process PID > 1 and 0 < seconds <= 300")
    root = Path("/proc") / str(args.pid)
    identity = (root / "stat").read_text().split(") ", 1)[1].split()[19]
    started = time.monotonic()
    samples = []
    while time.monotonic() - started < args.seconds:
        try:
            if (root / "stat").read_text().split(") ", 1)[1].split()[19] != identity:
                break
        except OSError:
            break
        records = {}
        for path in Path("/proc").iterdir():
            if not path.name.isdigit():
                continue
            try:
                raw = (path / "stat").read_text()
                fields = raw.split(") ", 1)[1].split()
                records[int(path.name)] = (path, int(fields[1]), fields)
            except (OSError, ValueError, IndexError):
                continue
        owned = {args.pid}
        while True:
            descendants = {pid for pid, (_, parent, _) in records.items() if parent in owned}
            if descendants <= owned:
                break
            owned |= descendants
        snapshot = {"offset_seconds": round(time.monotonic() - started, 3), "processes": []}
        for pid in sorted(owned):
            if pid not in records:
                continue
            path, parent, fields = records[pid]
            record = {"pid": pid, "ppid": parent, "state": fields[0], "user_ticks": int(fields[11]), "system_ticks": int(fields[12])}
            # Protected stack/syscall reads from a sibling can generate Yama
            # denials and audit work. Observe public state without weakening
            # ptrace policy or repeatedly provoking those denials.
            for name in ("wchan",):
                try:
                    record[name] = (path / name).read_text().strip()
                except OSError as exc:
                    record[name + "_unavailable"] = exc.errno
            try:
                record["command"] = (path / "cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace")
            except OSError:
                pass
            snapshot["processes"].append(record)
        samples.append(snapshot)
        time.sleep(.2)
    args.output.write_bytes((json.dumps({"root_pid": args.pid, "root_start_ticks": identity, "samples": samples}, indent=2) + "\n").encode())


if __name__ == "__main__":
    main()
