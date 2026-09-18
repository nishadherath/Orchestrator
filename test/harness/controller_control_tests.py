#!/usr/bin/env python3
"""R3 offline acceptance tests for the durable Controller control plane."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTROL_PATH = ROOT / "tools" / "controller_control.py"
spec = importlib.util.spec_from_file_location("controller_control", CONTROL_PATH)
assert spec and spec.loader
control = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = control
spec.loader.exec_module(control)


def check(name: str, condition: bool, detail: str = "") -> None:
    if not condition:
        raise AssertionError(f"{name}: {detail}")
    print(f"PASS {name}")


def run_cli(project: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CONTROL_PATH), "--project", str(project), *arguments],
        cwd=ROOT, text=True, capture_output=True, timeout=20,
    )


def test_truth_table(project: Path) -> None:
    check("default-auto", control.resolve(project).as_dict() == {
        "mode": "auto", "source": "shipped-default", "state_revision": 0,
        "task_revision": None, "session_id": None,
    })
    control.set_mode(project, "project", "on")
    control.set_mode(project, "session", "off", session_id="s1")
    control.set_mode(project, "task", "auto", task_revision="t1")
    expected = [
        (dict(), "on", "project"),
        (dict(session_id="s1"), "off", "session"),
        (dict(session_id="s1", task_revision="t1"), "auto", "task"),
        (dict(explicit_mode="on", session_id="s1", task_revision="t1"), "on", "explicit"),
        (dict(explicit_mode="auto", session_id="s1", task_revision="t1"), "auto", "explicit"),
    ]
    for kwargs, mode, source in expected:
        decision = control.resolve(project, **kwargs)
        check(f"precedence-{source}-{mode}", decision.mode == mode and decision.source == source)


def test_session_lifecycle(project: Path) -> None:
    # A compaction keeps the same durable session/task identifiers. A fresh
    # session has a new id and therefore inherits only the project value.
    control.set_mode(project, "project", "off")
    control.set_mode(project, "session", "on", session_id="compact-me")
    control.set_mode(project, "task", "auto", task_revision="task-rev-a")
    before = control.resolve(project, session_id="compact-me", task_revision="task-rev-a")
    after_compaction = control.resolve(project, session_id="compact-me", task_revision="task-rev-a")
    fresh = control.resolve(project, session_id="fresh-session", task_revision="task-rev-b")
    check("compaction-retains-task", before == after_compaction and before.source == "task")
    check("fresh-session-project-only", fresh.mode == "off" and fresh.source == "project")


def test_stale_and_clear(project: Path) -> None:
    initial = control.load_state(project)["revision"]
    state = control.set_mode(project, "session", "on", session_id="cancelled",
                             expected_revision=initial)
    try:
        control.set_mode(project, "project", "off", expected_revision=initial)
    except control.StaleControlError:
        pass
    else:
        raise AssertionError("stale-control: stale write was accepted")
    check("stale-control", control.load_state(project)["revision"] == state["revision"])
    control.clear_mode(project, "session", session_id="cancelled")
    check("clear-cancels-scope", "cancelled" not in control.load_state(project)["sessions"])


def test_in_flight_boundary(project: Path) -> None:
    control.set_mode(project, "project", "off")
    started = control.resolve(project)
    control.set_mode(project, "project", "on")
    next_boundary = control.resolve(project)
    check("in-flight-snapshot-stable", started.mode == "off" and next_boundary.mode == "on" and
          started.state_revision < next_boundary.state_revision)


def test_two_process_race(project: Path) -> None:
    command = [sys.executable, str(CONTROL_PATH), "--project", str(project), "set",
               "--scope", "project", "--expected-revision", "0"]
    first = subprocess.Popen(command + ["--mode", "on"], cwd=ROOT, text=True,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    second = subprocess.Popen(command + ["--mode", "off"], cwd=ROOT, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    first_out, first_err = first.communicate(timeout=20)
    second_out, second_err = second.communicate(timeout=20)
    results = sorted((first.returncode, second.returncode))
    state = control.load_state(project)
    check("two-process-race", results == [0, 2] and state["revision"] == 1 and
          state["project"]["mode"] in ("on", "off"),
          f"codes={results}, first={first_out}{first_err}, second={second_out}{second_err}")


def test_cli_and_no_dispatch(project: Path) -> None:
    source = CONTROL_PATH.read_text(encoding="utf-8")
    forbidden = ("evaluation_live", "system_controller", "claudep", "subprocess", "anthropic")
    check("provider-free-import-closure", all(f"import {name}" not in source and
          f"from {name}" not in source for name in forbidden))
    result = run_cli(project, "set", "--scope", "project", "--mode", "auto")
    payload = json.loads(result.stdout)
    resolved = run_cli(project, "resolve", "--explicit", "off")
    resolved_payload = json.loads(resolved.stdout)
    check("cli-parity", result.returncode == 0 and payload["paid_work_started"] is False and
          payload["state"]["project"]["source"]["kind"] == "operator-cli" and
          resolved_payload["decision"]["mode"] == "off" and
          resolved_payload["decision"]["source"] == "explicit")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="controller-control-") as raw:
        root = Path(raw)
        test_truth_table(root / "truth")
        test_session_lifecycle(root / "lifecycle")
        test_stale_and_clear(root / "stale")
        test_in_flight_boundary(root / "boundary")
        test_two_process_race(root / "race")
        test_cli_and_no_dispatch(root / "cli")
    print("controller control R3: 14/14 passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
