#!/usr/bin/env python3
"""Attest the disposable N4 WSL actor boundary without a paid worker call.

The probe launches the *actual* native Claude CLI far enough to inspect its
MCP/tool initialization. Its empty actor home has no credentials; a zero-token
authentication failure is expected. N5 must perform a fresh attestation and
still needs a separately authorised live campaign runner.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import json
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path, PurePosixPath

from worker_evaluation import ROOT, freeze

CORPUS = ROOT / "test" / "fixtures" / "worker_n4"
OUTPUT = ROOT / "test" / "results" / "2026-09-24-worker-n4-wsl-host.json"
RUNTIME = PurePosixPath("/opt/orchestrator-worker-runtime")
ACTOR_BASE = "/var/lib/orchestrator-worker-n4/actors/"
RUNTIME_FILES = (
    "bin/node", "bin/claude", "bin/worker-wsl-namespace", "actor-probe.py",
    "worker_wsl_materialize.py", "worker_wsl_collect.py", "worker_wsl_grade.py",
    "transport-probe.py",
    "actor-mcp.json", "lib/node_modules/@nanonets/graft/dist/cli.js",
)
SOURCE_FILES = (
    "tools/setup_worker_wsl.sh", "tools/worker_wsl_stage.sh",
    "tools/worker_wsl_namespace.sh", "tools/worker_wsl_actor_probe.py",
    "tools/worker_wsl_materialize.py", "tools/worker_wsl_collect.py",
    "tools/worker_wsl_grade.py",
    "tools/worker_wsl_transport_probe.py",
    "tools/worker_wsl_transport.py",
    "tools/worker_wsl_adapter_probe.py",
    "tools/worker_wsl_attestation.py",
)
GRAFT_TOOLS = {"mcp__graft__" + name for name in (
    "graft_check_freshness", "graft_repo_map", "graft_find_code",
    "graft_file_api", "graft_trace_calls", "graft_find_all")}
REQUIRED_CHECKS = {
    "acceptance_write_denied", "actor_edit_observed", "actor_read_write",
    "actor_root_creation_denied", "actor_uid", "allowed_edit_collected",
    "claude_actor_cwd", "claude_graft_connected", "claude_graft_six_tools",
    "claude_native_runs", "claude_no_credentials", "claude_no_execution_tools",
    "claude_no_inherited_plugins", "claude_no_paid_call",
    "claude_only_expected_tools", "evaluator_direct_denied",
    "evaluator_symlink_denied", "graft_actor_visible", "graft_evaluator_absent",
    "graft_parent_rejected", "graft_six_tools", "interop_socket_hidden",
    "namespace_process_stopped", "proc_root_no_escape",
    "protected_actor_change_rejected", "protected_source_untouched",
    "recursive_search_denied", "rejected_collection_did_not_write",
    "sanitized_environment", "windows_c_unmounted", "windows_d_unmounted",
    "windows_transport_graft_connected", "windows_transport_six_tools",
    "windows_transport_zero_charge", "windows_transport_source_unchanged",
    "windows_transport_path", "concurrent_source_change_rejected",
    "source_change_preserved", "windows_transport_edit_collected",
    "windows_transport_acceptance_untouched",
    "isolated_grade_acceptance", "isolated_grade_oracle_hidden",
    "isolated_grade_digest_rejected", "isolated_grade_output_capped",
    "windows_isolated_grade_bridge", "isolated_grade_partial_score",
    "isolated_grade_no_edit_rule", "isolated_grade_actor_digest_rejected",
    "sibling_actor_hidden",
}


class AttestationError(RuntimeError):
    """A host fact is unavailable or violates the worker isolation contract."""


def canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@contextlib.contextmanager
def temporary_actor(prefix: str):
    """Retry a Windows/WSL handle-release race without leaving probe inputs."""
    parent = ROOT / "test" / "results"
    parent.mkdir(parents=True, exist_ok=True)
    source = Path(tempfile.mkdtemp(prefix=prefix, dir=parent)).resolve()
    if source.is_symlink() or not source.is_relative_to(parent.resolve()):
        raise AttestationError("temporary probe escaped results directory")
    try:
        yield source
    finally:
        for attempt in range(12):
            if source.is_symlink() or not source.resolve().is_relative_to(parent.resolve()):
                raise AttestationError("temporary probe cleanup target changed")
            try:
                shutil.rmtree(source)
                break
            except FileNotFoundError:
                break
            except OSError as exc:
                if attempt == 11:
                    raise AttestationError("temporary bridge cleanup failed") from exc
                time.sleep(0.25)


def wsl(*args: str, timeout: int = 120) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(["wsl.exe", "-u", "root", "--", "bash", "-lc",
                               shlex.join(args)],
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AttestationError("WSL command unavailable or timed out") from exc


def checked(*args: str, timeout: int = 120) -> str:
    result = wsl(*args, timeout=timeout)
    if result.returncode:
        raise AttestationError(f"WSL {args[0]} exited {result.returncode}: "
                               + (result.stderr or result.stdout)[-300:])
    return result.stdout.strip()


def runtime_hashes() -> dict[str, str]:
    paths = [str(RUNTIME / name) for name in RUNTIME_FILES]
    lines = checked("sha256sum", *paths).splitlines()
    if len(lines) != len(paths):
        raise AttestationError("incomplete runtime fingerprint")
    values = {}
    for name, line, path in zip(RUNTIME_FILES, lines, paths):
        fields = line.split(maxsplit=1)
        if len(fields) != 2 or fields[1].lstrip("*") != path:
            raise AttestationError("runtime fingerprint path mismatch")
        values[name] = fields[0]
    # Graft loads native parser modules from transitive dependencies; hashing
    # only its entry point would miss an altered .node binary.
    tree = r'''
import hashlib, os, pathlib, sys
root = pathlib.Path(sys.argv[1])
digest = hashlib.sha256()
for directory, directories, files in os.walk(root, followlinks=False):
    directories.sort()
    for name in sorted(directories + files):
        path = pathlib.Path(directory) / name
        relative = path.relative_to(root).as_posix().encode()
        digest.update(len(relative).to_bytes(4, "big") + relative)
        if path.is_symlink():
            data = os.readlink(path).encode()
        elif path.is_file():
            data = hashlib.sha256(path.read_bytes()).digest()
        else:
            data = b"directory"
        digest.update(len(data).to_bytes(8, "big") + data)
print(digest.hexdigest())
'''
    values["graft_package_tree"] = checked("python3", "-c", tree,
        str(RUNTIME / "lib/node_modules/@nanonets/graft"))
    return values


def validate(value: dict, *, check_host: bool) -> bool:
    if not isinstance(value, dict):
        return False
    digest = value.get("evidence_sha256")
    body = {k: v for k, v in value.items() if k != "evidence_sha256"}
    if digest != hashlib.sha256(canonical(body)).hexdigest():
        return False
    if value.get("schema_version") != 1 or value.get("result") != "PASS":
        return False
    if value.get("manifest_sha256") != freeze(CORPUS)["manifest_sha256"]:
        return False
    checks = value.get("checks")
    if (not isinstance(checks, dict) or set(checks) != REQUIRED_CHECKS
            or not all(v is True for v in checks.values())):
        return False
    if value.get("source_hashes") != {name: sha(ROOT / name) for name in SOURCE_FILES}:
        return False
    if check_host and value.get("runtime_hashes") != runtime_hashes():
        return False
    return True


def run() -> dict:
    manifest = freeze(CORPUS)
    source_hashes = {name: sha(ROOT / name) for name in SOURCE_FILES}
    stage = checked("wslpath", "-a", (ROOT / "tools" / "worker_wsl_stage.sh")
                    .as_posix())
    actor = checked("bash", stage).splitlines()[-1]
    if not actor.startswith(ACTOR_BASE) or not actor[len(ACTOR_BASE):].startswith("probe-"):
        raise AttestationError("stage returned an invalid actor root")

    launcher = str(RUNTIME / "bin" / "worker-wsl-namespace")
    probe = wsl(launcher, actor, "--", "/usr/bin/python3",
                str(RUNTIME / "actor-probe.py"), timeout=150)
    try:
        report = json.loads(probe.stdout.strip())
    except json.JSONDecodeError as exc:
        raise AttestationError("actor probe returned no JSON: " + probe.stderr[-300:]) from exc
    if probe.returncode or report.get("result") != "PASS":
        raise AttestationError("actor boundary probe failed: " + json.dumps(report)[:400])

    transport_probe = wsl("python3", str(RUNTIME / "transport-probe.py"), timeout=60)
    try:
        transport_report = json.loads(transport_probe.stdout.strip())
    except json.JSONDecodeError as exc:
        raise AttestationError("transport probe returned no JSON: "
                               + transport_probe.stderr[-300:]) from exc
    if transport_probe.returncode or transport_report.get("result") != "PASS":
        raise AttestationError("materialize/collect probe failed: "
                               + json.dumps(transport_report)[:400])

    # Use the same non-greedy option syntax as WorkerAdapter.command(). The
    # unauthenticated actor can initialize tools but cannot make a paid call.
    claude_args = [str(RUNTIME / "bin" / "claude"), "-p", "probe",
                   "--output-format=stream-json", "--verbose", "--model", "sonnet",
                   "--effort", "low", "--max-budget-usd", "0.01", "--restricted",
                   "--strict-mcp-config",
                   f"--mcp-config={RUNTIME / 'actor-mcp.json'}",
                   "--no-session-persistence", "--permission-mode=acceptEdits",
                   "--permission-prompts=none", "--tools=Read,Edit,Write,Glob,Grep",
                   "--allowedTools=" + ",".join(sorted(GRAFT_TOOLS))]
    started = wsl(launcher, actor, "--", *claude_args, timeout=45)
    try:
        events = [json.loads(line) for line in started.stdout.splitlines() if line.strip()]
        init = next(row for row in events if row.get("type") == "system"
                    and row.get("subtype") == "init")
        result = next(row for row in reversed(events) if row.get("type") == "result")
    except (ValueError, StopIteration) as exc:
        raise AttestationError("Claude did not produce an init and terminal event") from exc
    names = set(init.get("tools", []))
    mcp = init.get("mcp_servers")
    cli_checks = {
        "claude_actor_cwd": init.get("cwd") == actor,
        "claude_graft_connected": mcp == [{"name": "graft", "status": "connected"}],
        "claude_graft_six_tools": GRAFT_TOOLS <= names,
        "claude_no_execution_tools": not names.intersection({"Bash", "PowerShell", "Task",
                                                         "WebFetch", "WebSearch"}),
        "claude_only_expected_tools": names <= GRAFT_TOOLS | {"Read", "Edit", "Write",
                                                             "Glob", "Grep"},
        "claude_no_inherited_plugins": init.get("plugins") == [],
        "claude_no_credentials": init.get("apiKeySource") == "none",
        "claude_no_paid_call": (started.returncode != 0
                               and result.get("total_cost_usd") == 0
                               and result.get("usage", {}).get("input_tokens") == 0
                               and result.get("usage", {}).get("output_tokens") == 0),
    }
    # This invokes the same Windows bridge and WSL namespace path that the
    # later TaskExecutor adapter will use. Its temporary actor has no secret.
    from worker_adapter import WorkerAdapter, WorkerRequest
    from worker_wsl_transport import WslTransport

    with temporary_actor("worker-n5-bridge-") as source:
        (source / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
        (source / "public_check.py").write_text("assert True\n", encoding="utf-8")
        (source / "ISSUE.md").write_text("Probe host startup.\n", encoding="utf-8")
        (source / "acceptance.json").write_text('{"schema_version":1}\n', encoding="utf-8")
        request = WorkerRequest(source, "Probe host startup", ("app.py",),
                                "worker-sonnet-low", 0.01, "N5 host probe",
                                timeout_s=30, admission_token="probe",
                                invocation_id=uuid.uuid4().hex, revision_id="probe",
                                decision_digest="probe", intent_digest="probe")
        command = WorkerAdapter(ROOT / ".mcp.json").command(request)
        bridge = WslTransport().invoke(invocation_id=request.invocation_id,
                                       command=command, source=source, timeout=30)
        try:
            bridge_events = [json.loads(line) for line in bridge.stdout.splitlines()
                             if line.strip()]
            bridge_init = next(row for row in bridge_events if row.get("type") == "system"
                               and row.get("subtype") == "init")
            bridge_result = next(row for row in reversed(bridge_events)
                                 if row.get("type") == "result")
        except (ValueError, StopIteration) as exc:
            raise AttestationError("Windows-to-WSL bridge emitted no terminal startup") from exc
        bridge_checks = {
            "windows_transport_graft_connected": bridge_init.get("mcp_servers") == [
                {"name": "graft", "status": "connected"}],
            "windows_transport_six_tools": GRAFT_TOOLS <= set(bridge_init.get("tools", [])),
            "windows_transport_zero_charge": bridge_result.get("total_cost_usd") == 0
            and bridge_result.get("usage", {}).get("input_tokens") == 0,
            "windows_transport_source_unchanged": (source / "app.py").read_text(
                encoding="utf-8") == "VALUE = 1\n",
        }
        bridge_checks["windows_transport_path"] = all(bridge_checks.values())
        if not bridge_checks["windows_transport_six_tools"]:
            raise AttestationError("bridge startup tools: "
                                   + ",".join(sorted(bridge_init.get("tools", []))))
        # The live evaluator works on a Windows actor directory. Exercise the
        # same collector across the 9p boundary with a local actor edit.
        edit_name = "inv-" + uuid.uuid4().hex
        linux_source = checked("wslpath", "-a", source.as_posix())
        staged = json.loads(checked("python3", str(RUNTIME / "worker_wsl_materialize.py"),
                                   "--source", linux_source, "--name", edit_name))
        edited = wsl(launcher, staged["actor_root"], "--", "/usr/bin/python3", "-c",
                     "from pathlib import Path; Path('app.py').write_text('VALUE = 2\\n')",
                     timeout=30)
        if edited.returncode:
            raise AttestationError("Windows actor edit probe failed: " + edited.stderr[-200:])
        collection = json.loads(checked("python3", str(RUNTIME / "worker_wsl_collect.py"),
                                        "--name", edit_name, "--source", linux_source))
        bridge_checks["windows_transport_edit_collected"] = collection["changed"] and (
            source / "app.py").read_text(encoding="utf-8") == "VALUE = 2\n"
        bridge_checks["windows_transport_acceptance_untouched"] = (
            (source / "acceptance.json").read_text(encoding="utf-8")
            == '{"schema_version":1}\n')
        # The paid screen must never execute candidate code as the Windows
        # evaluator user. Grade two cases via fresh WSL actor namespaces.
        (source / "app.py").write_text(
            "import json, sys\n"
            "for line in sys.stdin:\n"
            "    print(json.dumps({'value': json.loads(line)['value'] * 2}))\n",
            encoding="utf-8")
        oracle = source / "oracle.json"
        oracle.write_text(json.dumps({"schema_version": 1, "cases": [
            {"input": {"value": 2}, "expected": {"value": 4}, "weight": 1,
             "milestone": "first", "critical": False},
            {"input": {"value": 3}, "expected": {"value": 6}, "weight": 1,
             "milestone": "second", "critical": False}]}) + "\n", encoding="utf-8")
        oracle_linux = checked("wslpath", "-a", oracle.as_posix())
        grade_name = "inv-" + uuid.uuid4().hex
        grade_actor = json.loads(checked(
            "python3", str(RUNTIME / "worker_wsl_materialize.py"),
            "--source", linux_source, "--name", grade_name))["actor_root"]
        bridge_checks["sibling_actor_hidden"] = (
            wsl(launcher, grade_actor, "--", "/usr/bin/test", "-e",
                staged["actor_root"] + "/app.py", timeout=30).returncode != 0)
        grade_args = ("python3", str(RUNTIME / "worker_wsl_grade.py"),
                      "--actor-name", grade_name, "--oracle-source", oracle_linux,
                      "--oracle-sha256", sha(oracle), "--root-state", "accepted")
        grade = json.loads(checked(*grade_args, timeout=60))
        bridge_checks["isolated_grade_acceptance"] = (
            grade["acceptance"] is True and grade["quality"] == 100
            and grade["case_count"] == 2 and grade["oracle_sha256"] == sha(oracle))
        bridge_checks["isolated_grade_oracle_hidden"] = (
            wsl(launcher, grade_actor, "--", "/usr/bin/test", "-r", oracle_linux,
                timeout=30).returncode != 0)
        from worker_wsl_transport import TransportError, grade_isolated
        app_digest = sha(source / "app.py")
        bridged_grade = grade_isolated(source, oracle, sha(oracle), app_digest,
                                      "accepted")
        bridge_checks["windows_isolated_grade_bridge"] = (
            bridged_grade["acceptance"] is True
            and bridged_grade["oracle_sha256"] == sha(oracle))
        try:
            grade_isolated(source, oracle, sha(oracle), "0" * 64, "accepted")
        except TransportError:
            bridge_checks["isolated_grade_actor_digest_rejected"] = True
        else:
            bridge_checks["isolated_grade_actor_digest_rejected"] = False
        partial_oracle = source / "oracle_partial.json"
        partial_oracle.write_text(json.dumps({"schema_version": 1, "cases": [
            {"input": {"value": 2}, "expected": {"value": 4}, "weight": 1,
             "milestone": "first", "critical": False},
            {"input": {"value": 3}, "expected": {"value": 7}, "weight": 1,
             "milestone": "second", "critical": True}]}) + "\n", encoding="utf-8")
        partial = grade_isolated(source, partial_oracle, sha(partial_oracle),
                                 app_digest, "accepted")
        bridge_checks["isolated_grade_partial_score"] = (
            partial["acceptance"] is False and partial["quality"] == 50
            and partial["critical_error"] is True
            and partial["false_success"] is True
            and partial["milestones"] == ["first"])
        no_edit_oracle = source / "oracle_no_edit.json"
        no_edit_oracle.write_text(json.dumps({"schema_version": 1,
            "cases": [{"input": {"value": 2}, "expected": {"value": 4},
                       "weight": 1, "milestone": "first", "critical": False}],
            "no_edit_baseline_sha256": "0" * 64}) + "\n", encoding="utf-8")
        no_edit = grade_isolated(source, no_edit_oracle, sha(no_edit_oracle),
                                 app_digest, "accepted")
        bridge_checks["isolated_grade_no_edit_rule"] = (
            no_edit["acceptance"] is False and no_edit["quality"] == 0
            and no_edit["critical_error"] is True
            and no_edit["false_success"] is True)
        bad_grade = wsl(*grade_args[:-4], "--oracle-sha256", "0" * 64,
                        "--root-state", "accepted", timeout=30)
        bridge_checks["isolated_grade_digest_rejected"] = (
            bad_grade.returncode != 0 and not bad_grade.stdout.strip())
        (source / "app.py").write_text(
            "import sys\nsys.stdout.write('x' * 70000)\n", encoding="utf-8")
        noisy_name = "inv-" + uuid.uuid4().hex
        checked("python3", str(RUNTIME / "worker_wsl_materialize.py"),
                "--source", linux_source, "--name", noisy_name)
        noisy = wsl("python3", str(RUNTIME / "worker_wsl_grade.py"),
                    "--actor-name", noisy_name, "--oracle-source", oracle_linux,
                    "--oracle-sha256", sha(oracle), "--root-state", "accepted",
                    timeout=30)
        bridge_checks["isolated_grade_output_capped"] = (
            noisy.returncode != 0 and "output limit" in noisy.stderr)
    checks = {**report["checks"], **transport_report["checks"],
              **cli_checks, **bridge_checks}
    evidence = {
        "schema_version": 1,
        "recorded_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "manifest_sha256": manifest["manifest_sha256"],
        "actor_root": actor,
        "boundary": "WSL private mount+PID namespaces, uid 65534, Linux ext4 actor/evaluator",
        "runtime_hashes": runtime_hashes(),
        "source_hashes": source_hashes,
        "checks": checks,
        "result": "PASS" if all(checks.values()) else "FAIL",
        "limits": ["No authenticated provider request or paid worker edit occurred.",
                   "N5 requires a fresh attestation, credential configuration and live runner."],
    }
    evidence["evidence_sha256"] = hashlib.sha256(canonical(evidence)).hexdigest()
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    try:
        if args.check:
            valid = validate(json.loads(args.output.read_text(encoding="utf-8")),
                             check_host=True)
            print("PASS: WSL host attestation current" if valid else
                  "FAIL: WSL host attestation stale or invalid")
            return 0 if valid else 1
        evidence = run()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8", newline="\n")
        print(f"{evidence['result']}: {len(evidence['checks'])} WSL host checks; "
              f"manifest {evidence['manifest_sha256'][:12]}")
        return 0 if evidence["result"] == "PASS" else 1
    except (OSError, ValueError, KeyError, AttestationError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
