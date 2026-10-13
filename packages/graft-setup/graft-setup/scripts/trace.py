"""Run a skill helper unchanged, recording stage timing and safe Python wait samples."""
from __future__ import annotations

import sys
import time


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in {"diagnose", "refresh", "probe_mcp"}:
        print("Usage: python trace.py {diagnose|refresh|probe_mcp} <helper arguments>", file=sys.stderr)
        return 2
    isolated = "--isolate-imports" in sys.argv[2:]
    if isolated:
        sys.argv.remove("--isolate-imports")
        import os
        directory = os.path.dirname(os.path.abspath(__file__))
        # Standard-library imports otherwise probe the mounted script directory
        # first. Keep configured paths; remove only this helper directory.
        sys.path[:] = [entry for entry in sys.path if not isinstance(entry, str)
                       or os.path.normcase(os.path.abspath(entry)) != os.path.normcase(directory)]
    started = time.monotonic()
    cpu_started = time.process_time()
    # Emit before filesystem-backed imports. A late marker cannot explain
    # deadlines consumed by loading the helper itself.
    sys.stderr.write(f'{{"trace":true,"phase":"bootstrap","started_unix":{time.time()},"offset_seconds":0.0}}\n')
    sys.stderr.flush()
    import functools
    import json
    import runpy
    import threading
    from pathlib import Path
    if isolated:
        import importlib.util
        spec = importlib.util.spec_from_file_location("graft_common", Path(directory) / "graft_common.py")
        graft_common = importlib.util.module_from_spec(spec)
        sys.modules["graft_common"] = graft_common
        spec.loader.exec_module(graft_common)
    else:
        import graft_common
    main_thread = threading.get_ident()
    stopped = threading.Event()
    lock = threading.Lock()

    def emit(event):
        with lock:
            print(json.dumps({"trace": True, "offset_seconds": round(time.monotonic() - started, 6), **event}), file=sys.stderr, flush=True)

    emit({"phase": "imports_end", "process_cpu_seconds": round(time.process_time() - cpu_started, 6)})

    def wrap(name):
        original = getattr(graft_common, name)

        @functools.wraps(original)
        def timed(*args, **kwargs):
            before = time.monotonic()
            cpu = time.process_time()
            event = {"stage": name}
            if name == "run":
                # Identify command kinds without recording arguments, source,
                # environment values or credentials supplied by the operator.
                event["command_kind"] = next((kind for kind in ("--version", "--help", "build", "check") if kind in args[0]), "other")
            emit({**event, "phase": "start"})
            try:
                return original(*args, **kwargs)
            finally:
                emit({**event, "phase": "end", "wall_seconds": round(time.monotonic() - before, 6),
                      "process_cpu_seconds": round(time.process_time() - cpu, 6)})
        setattr(graft_common, name, timed)

    for name in ("repo_path", "local_path", "no_links", "capabilities", "run", "graph_summary"):
        wrap(name)

    def sample():
        while not stopped.wait(1):
            frame = sys._current_frames().get(main_thread)
            locations = []
            while frame is not None and len(locations) < 12:
                locations.append({"file": Path(frame.f_code.co_filename).name, "function": frame.f_code.co_name, "line": frame.f_lineno})
                frame = frame.f_back
            emit({"phase": "sample", "python_stack": locations})

    thread = threading.Thread(target=sample, daemon=True)
    thread.start()
    script = Path(__file__).with_name(sys.argv[1] + ".py")
    sys.argv = [str(script), *sys.argv[2:]]
    try:
        runpy.run_path(str(script), run_name="__main__")
    finally:
        stopped.set()
        thread.join(timeout=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
