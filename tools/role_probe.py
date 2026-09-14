#!/usr/bin/env python3
"""Per-role cost probe (docs/PLAN.md task 9.7): one Frame, Verify, Generate
or Critique call on a toy problem, at the role's quick-mode cell, with its
brief, measured.

    python3 tools/role_probe.py --project <consumer project> --role frame --record
    python3 tools/role_probe.py --project <consumer project> --role all --record

The toy problem is T10 (test/fixtures/benchmark/T10), and the input slices
come from test/fixtures/system/valid.jsonl, the example ledger, so each
role is probed on exactly the records its contract names and nothing else.
The call is `claude -p` invoked directly with --model and --effort (E23),
which is how the Stage 10 Controller will invoke cells; there is no
forwarder, so the reported total_cost_usd is the role's own cost.

What is recorded, per role: cost, input and output tokens, cache
creation and read, wall clock, whether the reply parsed as JSONL, and
whether every record validated against src/System/schemas/. These are the
parameters Stage 11's pre-registration needs; the schema-validity rate is
a bonus measurement of whether a role can be made to speak records at all.

The Verify probe needs the T10 repository on disk: it is copied to
<project>/probe-T10/ if not already there, and the Verifier is told its
files live there. The other three roles need no tools.
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SYSTEM = REPO_ROOT / "src" / "System"
LEDGER_EXAMPLE = REPO_ROOT / "test" / "fixtures" / "system" / "valid.jsonl"
T10_REPO = REPO_ROOT / "test" / "fixtures" / "benchmark" / "T10" / "repo"
RESULTS_DIR = REPO_ROOT / "test" / "results"

sys.path.insert(0, str(REPO_ROOT / "tools"))
from system_prompts import OUTPUT_RULE, as_jsonl, role_section, schema_summary, technique_brief  # noqa: E402

# src/System/ROLES.md, quick-mode column. Kept in step by hand; the probe
# prints the cell it used so a drift is visible in the result file.
CELLS = {
    "frame": ("framer", "opus", "high"),
    "verify": ("verifier", "sonnet", "medium"),
    "generate": ("generator", "sonnet", "high"),
    "critique": ("critic", "opus", "medium"),
}

PERMISSION_ARGS = ["--permission-mode", "acceptEdits", "--allowedTools", "Bash(python3 *),Bash(python *)"]


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_records", REPO_ROOT / "tools" / "validate_records.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ledger_records(*types: str, version: int | None = None) -> list[dict]:
    recs = [json.loads(l) for l in LEDGER_EXAMPLE.read_text(encoding="utf-8").splitlines() if l.strip()]
    return [r for r in recs if r["type"] in types and (version is None or r["ledger_version"] <= version)]


def build_prompt(role: str, project: Path) -> tuple[str, list[str]]:
    """Returns (prompt, expected output record types)."""
    if role == "frame":
        problem = ledger_records("ProblemRecord")
        brief = role_section("Framer")
        return (brief + "\n\n" + schema_summary("PremiseRecord", "FrameRecord", "CandidateRecord")
                + "\n\nInput slice (the ProblemRecord; the false-premise catalogue is empty, this is the first run):\n"
                + as_jsonl(problem)
                + "\n\nProduce ledger version 1: every PremiseRecord, one FrameRecord, and the B0 CandidateRecord."
                + OUTPUT_RULE,
                ["PremiseRecord", "FrameRecord", "CandidateRecord"])
    if role == "verify":
        premise = [r for r in ledger_records("PremiseRecord") if r["id"] == "prem-002"]
        problem = ledger_records("ProblemRecord")
        brief = role_section("Verifier")
        return (brief + "\n\n" + schema_summary("MeasurementRecord")
                + "\n\nInput slice (one premise to measure, and the problem's context):\n"
                + as_jsonl(problem + premise)
                + f"\n\nThe repository the premise concerns is in `probe-T10/` under the current directory: "
                  "accounts.py, legacy_ids.py, downstream.py, test_accounts.py, test_downstream.py. Quick mode: "
                  "one tool call, no new code. Run the premise's cheapest_verification and write one "
                  "MeasurementRecord with the artefact path you read the result from."
                + OUTPUT_RULE,
                ["MeasurementRecord"])
    if role == "generate":
        ledger = ledger_records("PremiseRecord", "FrameRecord", "CandidateRecord", version=2)
        ledger = [r for r in ledger if r["type"] != "CandidateRecord" or r["technique"] == "b0"]
        brief = role_section("Generator (template; the technique family is the parameter)")
        family = technique_brief("Subtract")
        return (brief + "\n\nYour technique brief:\n" + family + "\n\n" + schema_summary("CandidateRecord")
                + "\n\nInput slice (the frozen ledger at version 2, including B0; no retrieved patterns, the library is empty):\n"
                + as_jsonl(ledger)
                + "\n\nApply the brief against this ledger. Emit CandidateRecords citing ledger_version 2, or none if the trigger question has no answer here."
                + OUTPUT_RULE,
                ["CandidateRecord"])
    if role == "critique":
        ledger = ledger_records("PremiseRecord", "FrameRecord", version=2)
        cands = ledger_records("CandidateRecord")
        brief = role_section("Critic")
        return (brief + "\n\n" + schema_summary("CritiqueRecord")
                + "\n\nInput slice (the frozen ledger at version 2, and the tier's candidates including B0):\n"
                + as_jsonl(ledger + cands)
                + "\n\nWrite one CritiqueRecord per candidate."
                + OUTPUT_RULE,
                ["CritiqueRecord"])
    raise ValueError(role)


def run(role: str, project: Path, timeout: float) -> dict:
    _, model, effort = CELLS[role]
    if role == "verify":
        dest = project / "probe-T10"
        if not dest.exists():
            shutil.copytree(T10_REPO, dest)
    prompt, expected = build_prompt(role, project)
    cmd = ["claude", "-p", prompt, "--output-format", "json", "--model", model, "--effort", effort, *PERMISSION_ARGS]
    start = time.perf_counter()
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=project, timeout=timeout)
    wall = time.perf_counter() - start
    out: dict = {"role": role, "model": model, "effort": effort, "wall_clock_s": round(wall, 1),
                 "prompt_chars": len(prompt), "exit": proc.returncode, "expected_types": expected}
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        out.update({"error": "claude -p output was not JSON", "stdout_head": proc.stdout[:400], "stderr_head": proc.stderr[:400]})
        return out
    out["cost_usd"] = payload.get("total_cost_usd")
    out["duration_ms"] = payload.get("duration_ms")
    out["num_turns"] = payload.get("num_turns")
    usage = payload.get("usage", {})
    out["tokens"] = {k: usage.get(k) for k in ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")}
    result = payload.get("result", "") or ""
    out["reply_chars"] = len(result)

    # Parse the reply as JSONL, tolerating a code fence the rule forbade.
    lines = [l.strip() for l in result.strip().strip("`").splitlines() if l.strip() and not l.strip().startswith("```")]
    records, bad = [], 0
    for l in lines:
        try:
            records.append(json.loads(l))
        except json.JSONDecodeError:
            bad += 1
    out["records_parsed"] = len(records)
    out["lines_unparsed"] = bad
    v = load_validator()
    schemas = v.load_schemas()
    # Validate against the example ledger so references to it resolve.
    context = [("example", r) for r in ledger_records("ProblemRecord", "PremiseRecord", "FrameRecord", "CandidateRecord", "MeasurementRecord")]
    problems = v.validate_ledger(context + [(f"reply:{i+1}", r) for i, r in enumerate(records)], schemas)
    # A role re-emitting an id the example ledger already holds (prem-001 for
    # the Framer's first premise, meas-001 for the Verifier's measurement) is
    # expected here, since the roles are producing the records the example
    # was written to stand in for; it is not a schema defect. The first run
    # of this probe counted those collisions and overstated every role's
    # problem count (test/results/2026-09-14-role-probe-*.md, corrected
    # reading at the end of the file).
    problems = [p for p in problems if p.startswith("reply:") and "already used at example" not in p]
    out["schema_problems"] = len(problems)
    out["schema_problem_sample"] = problems[:8]
    out["types_returned"] = sorted({r.get("type") for r in records if isinstance(r, dict)})
    out["reply"] = result
    return out


def render(results: list[dict], when: str) -> str:
    lines = [f"# Per-role cost probes, {when}", "",
             "Task 9.7 (`docs/PLAN.md`). One call per role at its quick-mode cell from `src/System/ROLES.md`, "
             "with its brief, on T10 as the toy problem and `test/fixtures/system/valid.jsonl` as the input "
             "slices. Direct `claude -p --model --effort` invocation, no forwarder, so cost is the role's own. "
             "Cache figures are for a cold call; a fleet run shares the static prefix.", "",
             "| Role | Cell | Cost USD | In | Out | Cache create | Cache read | Wall s | Records | Unparsed lines | Schema problems | Types returned |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in results:
        t = r.get("tokens", {})
        lines.append(f"| {r['role']} | {r['model']}/{r['effort']} | {r.get('cost_usd', 'n/a')} | {t.get('input_tokens', '')} | "
                     f"{t.get('output_tokens', '')} | {t.get('cache_creation_input_tokens', '')} | {t.get('cache_read_input_tokens', '')} | "
                     f"{r['wall_clock_s']} | {r.get('records_parsed', '')} | {r.get('lines_unparsed', '')} | "
                     f"{r.get('schema_problems', '')} | {', '.join(r.get('types_returned', []))} |")
    for r in results:
        lines += ["", f"## {r['role']}", ""]
        if r.get("error"):
            lines += [f"Error: {r['error']}", "", "```", r.get("stdout_head", ""), r.get("stderr_head", ""), "```"]
            continue
        if r.get("schema_problem_sample"):
            lines += ["Schema problems (first eight):", ""] + [f"- {p}" for p in r["schema_problem_sample"]] + [""]
        lines += ["Reply:", "", "```", r.get("reply", ""), "```"]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--project", required=True, type=Path)
    ap.add_argument("--role", required=True, choices=[*CELLS, "all"])
    ap.add_argument("--timeout", type=float, default=900)
    ap.add_argument("--record", action="store_true", help="write test/results/<date>-role-probe-<roles>.md")
    ap.add_argument("--dry-run", action="store_true", help="print the prompt sizes and commands; run nothing")
    args = ap.parse_args(argv)
    roles = list(CELLS) if args.role == "all" else [args.role]
    if args.dry_run:
        for role in roles:
            prompt, expected = build_prompt(role, args.project)
            _, model, effort = CELLS[role]
            print(f"{role}: claude -p <{len(prompt)} chars> --output-format json --model {model} --effort {effort} "
                  f"{' '.join(PERMISSION_ARGS)}  -> expects {expected}")
        return 0
    if shutil.which("claude") is None:
        print("claude not on PATH", file=sys.stderr)
        return 2
    when = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    results = []
    for role in roles:
        r = run(role, args.project, args.timeout)
        results.append(r)
        print(f"{role}: cost {r.get('cost_usd')} wall {r['wall_clock_s']}s records {r.get('records_parsed')} "
              f"schema problems {r.get('schema_problems')}" + (f" ERROR {r['error']}" if r.get("error") else ""))
    if args.record:
        RESULTS_DIR.mkdir(exist_ok=True)
        out = RESULTS_DIR / f"{dt.datetime.now().strftime('%Y-%m-%d')}-role-probe-{'+'.join(roles)}.md"
        out.write_text(render(results, when), encoding="utf-8", newline="\n")
        print(f"recorded {out.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
