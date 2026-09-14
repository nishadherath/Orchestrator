"""Shared `claude -p` plumbing for the repository's harnesses and the Stage
10 Controller: the subprocess invocation, permission-flag constants, a
resumable checkpoint log, and the filename-collision guards result-writing
scripts need.

Responsible for: everything `test/harness/benchmark.py` and
`test/harness/score_routing.py` used to duplicate byte-for-byte
(`bundle_tag`, `unique_path`, `wilson_interval`, the `claude -p` subprocess
call and its error handling) plus `benchmark.py`'s `Checkpoint` class,
pulled out so `tools/system_controller.py` (docs/PLAN.md Stage 10) has one
place to get it from rather than a third hand-copied version. Both harnesses
now import from here instead of defining their own copies; `docs/PLAN.md`
task 10.1 is this file.

Deliberately does not: know about benchmark tasks, routing fixtures, or
ledger records. Those stay in their own callers. `describe_checkpoint_mismatch`
in `benchmark.py` and the fixture-hash comparison it layers on top of
`describe_identity_mismatch` below are a caller-specific example of the
pattern this module leaves room for.

The one non-obvious thing: `call_claude`'s argument order
(`--model`, then `--effort`, then `permission_args`, then `extra_args`) is
chosen so that passing exactly what each pre-refactor call site passed
reproduces its exact argv, which is how this refactor was verified not to
change behaviour (see the commit message for the before/after argv diff).
"""
from __future__ import annotations

import dataclasses
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

# claude -p starts in Manual permission mode by default (docs/en/permission-modes),
# which blocks Edit and Bash with nobody present to approve them. acceptEdits
# auto-approves file edits in the working directory; the explicit allowedTools
# entry admits the one Bash command a task.md asks a worker to self-check
# with. Both spellings of the interpreter are allowed since D41
# (docs/DECISIONS.md): only `python3 *` was, until two of nine T9 confirmation
# runs were voided by a worker typing `python` instead.
# --dangerously-skip-permissions is the documented pattern for "run fully
# unattended inside a container", but its own warning restricts it to an
# isolated container or VM without internet access, not a bare machine, so
# it is opt-in, never the default.
# Below the 32,767-character Windows command-line cap with room for every
# flag call_claude adds (a --json-schema literal is the longest, under 1k).
STDIN_PROMPT_THRESHOLD_CHARS = 30000

FORWARDER_PERMISSION_ARGS = ["--permission-mode", "acceptEdits", "--allowedTools", "Bash(python3 *),Bash(python *)"]
BYPASS_PERMISSION_ARGS = ["--dangerously-skip-permissions"]


@dataclasses.dataclass
class ClaudeCallResult:
    """What one `claude -p` invocation returned, or would have returned
    under --dry-run (in which case `result`, `cost_usd` and `extras` hold
    their zero values and `raw` is empty; only `cmd_shown` is meaningful)."""
    result: str
    cost_usd: float | None
    elapsed_s: float
    extras: dict
    raw: dict
    cmd_shown: str


def call_claude(prompt: str, *, cwd: Path, model: str | None = None, effort: str | None = None,
                 permission_args: list[str] = (), extra_args: list[str] = (),
                 json_schema: dict | None = None, max_budget_usd: float | None = None,
                 timeout: float = 300, dry_run: bool = False) -> ClaudeCallResult:
    """Invoke `claude -p <prompt> --output-format json`, with `--model`,
    `--effort`, `--json-schema`, `--max-budget-usd`, then any permission or
    extra flags, appended in that order.

    Raises RuntimeError on a non-zero exit, carrying the last 400 characters
    of stderr, matching what both prior call sites did. `extras` holds
    `usage`, `duration_ms` and `num_turns` from the response when present;
    callers that need only `result` and `cost_usd` (score_routing.py's
    original shape) can ignore it.

    `json_schema` and `max_budget_usd` are E25 (docs/FINDINGS.md, 2026-09-14):
    real `claude -p` flags, confirmed to exist via `--help` but not yet
    exercised live. `json_schema` is passed as a literal JSON string, per the
    help text's own example (not a file path). `system_controller.py` is the
    first caller of either; its docstring says what is still unverified.
    """
    # Windows caps a process's whole command line at 32,767 characters
    # (CreateProcess; WinError 206 "filename or extension is too long" when
    # exceeded). A Critique prompt carrying five candidates plus the ledger,
    # doubled by a retry, crossed it live (D56). A prompt over the threshold
    # goes to `claude -p` on stdin instead, the documented pipe usage;
    # shorter prompts keep the exact argv every earlier run used. E26 is
    # the live check that stdin carries a prompt this long intact.
    via_stdin = len(prompt) > STDIN_PROMPT_THRESHOLD_CHARS
    cmd = ["claude", "-p"] + ([] if via_stdin else [prompt]) + ["--output-format", "json"]
    if model:
        cmd += ["--model", model]
    if effort:
        cmd += ["--effort", effort]
    if json_schema is not None:
        cmd += ["--json-schema", json.dumps(json_schema, separators=(",", ":"))]
    if max_budget_usd is not None:
        cmd += ["--max-budget-usd", str(max_budget_usd)]
    cmd += list(permission_args)
    cmd += list(extra_args)
    cmd_shown = ("claude -p <prompt via stdin> " + " ".join(cmd[2:])) if via_stdin else (
        " ".join(cmd[:2]) + " <prompt> " + " ".join(cmd[3:]))

    if dry_run:
        return ClaudeCallResult(result="", cost_usd=None, elapsed_s=0.0, extras={}, raw={}, cmd_shown=cmd_shown)

    start = time.monotonic()
    proc = subprocess.run(cmd, input=prompt if via_stdin else None, capture_output=True, text=True,
                          encoding="utf-8", cwd=cwd, timeout=timeout)
    elapsed = time.monotonic() - start
    if proc.returncode != 0:
        # A budget abort (--max-budget-usd) reports on stdout as JSON with
        # an empty stderr; show whichever stream has the reason.
        detail = proc.stderr.strip()[-400:] or proc.stdout.strip()[-400:]
        raise RuntimeError(f"claude exited {proc.returncode}: {detail}")
    data = json.loads(proc.stdout)
    extras = {k: data.get(k) for k in ("usage", "duration_ms", "num_turns") if k in data}
    return ClaudeCallResult(result=str(data.get("result", "")), cost_usd=data.get("total_cost_usd"),
                             elapsed_s=elapsed, extras=extras, raw=data, cmd_shown=cmd_shown)


def bundle_tag(bundle: str) -> str:
    """Short filesystem-safe identifier for a bundle, used in result
    filenames. Without it, two runs on the same day silently overwrite each
    other's recorded evidence, which happened on 2026-09-06."""
    m = re.search(r"[0-9a-f]{7,40}", bundle)
    if m:
        return m.group(0)[:7]
    return re.sub(r"[^A-Za-z0-9]+", "-", bundle).strip("-")[:20] or "unknown"


def unique_path(path: Path) -> Path:
    """Return `path` unchanged if nothing is there yet, otherwise the first
    `-2`, `-3`, ... variant that is free.

    Last-resort guard, not a substitute for a caller's own tag helpers (a
    task or fixture subset, a model, a bundle): two runs can still share
    every tag (an identical rerun later the same day). A script whose
    entire purpose is recording evidence should never silently destroy
    evidence it already recorded (D34, D36, docs/DECISIONS.md)."""
    if not path.exists():
        return path
    n = 2
    while True:
        candidate = path.with_name(f"{path.stem}-{n}{path.suffix}")
        if not candidate.exists():
            return candidate
        n += 1


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95 percent Wilson score interval for a binomial proportion, z=1.96 by
    default. Preferred over a normal approximation because it stays inside
    [0, 1] and is not degenerate at n=0 or at successes in {0, n}, all of
    which occur at the small run counts this repository uses."""
    if n == 0:
        return (0.0, 1.0)
    p_hat = successes / n
    denom = 1 + z * z / n
    centre = (p_hat + z * z / (2 * n)) / denom
    margin = (z / denom) * ((p_hat * (1 - p_hat) / n + z * z / (4 * n * n)) ** 0.5)
    return (max(0.0, centre - margin), min(1.0, centre + margin))


def rmtree_if_exists(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def describe_identity_mismatch(old: dict, new: dict, fields: tuple[str, ...]) -> list[str]:
    """Human-readable reasons an existing checkpoint's meta does not match
    this invocation, over the given identity fields. Empty means safe to
    resume. Callers with an additional identity concern (benchmark.py's
    per-fixture content hash) append their own check to the returned list."""
    return [f"{key}: checkpoint has {old.get(key)!r}, this invocation has {new.get(key)!r}"
            for key in fields if old.get(key) != new.get(key)]


class Checkpoint:
    """Every completed run, appended to disk the moment it finishes, so an
    interrupted invocation (network drop, machine sleep, Ctrl-C) can resume
    mid-task, mid-cell, or mid-run on the next invocation instead of
    discarding already-paid-for work back to the start. A caller consults
    `prior_runs()` before making a call it might not need to repeat, and
    calls `record()` the moment each new one returns.

    The file is JSON Lines: one {"kind": "meta", ...} header written once,
    then one {"kind": "run", ...} line per completed run, keyed by an
    arbitrary three-part label (`benchmark.py` uses task/phase/cell; a
    caller with a different shape of resumable work picks its own three
    labels). A line that fails to parse (a partial write from a hard kill
    mid-append) is skipped with a warning rather than aborting the whole
    resume; everything before it is still trusted."""

    def __init__(self, path: Path):
        self.path = path
        self._runs: dict[tuple[str, str, str], list[dict]] = {}

    def prior_runs(self, label1: str, label2: str, label3: str) -> list[dict]:
        return self._runs.get((label1, label2, label3), [])

    def total_runs(self) -> int:
        return sum(len(v) for v in self._runs.values())

    def record(self, label1: str, label2: str, label3: str, result: dict) -> None:
        self._runs.setdefault((label1, label2, label3), []).append(result)
        self._append({"kind": "run", "task": label1, "phase": label2, "cell": label3, "result": result})

    def write_meta(self, meta: dict) -> None:
        self._append({"kind": "meta", "meta": meta})

    def _append(self, row: dict) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
            f.flush()
            os.fsync(f.fileno())

    @classmethod
    def load(cls, path: Path) -> tuple["Checkpoint", dict | None]:
        """Read an existing checkpoint, if any. Returns a Checkpoint
        populated with whatever prior runs it holds, and its stored meta
        dict (None if the file does not exist or has no meta line yet)."""
        cp = cls(path)
        meta = None
        if not path.exists():
            return cp, meta
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                print(f"warning: {path} line {lineno} did not parse (a partial write from an "
                      "interrupted run?); ignoring it, resuming from everything before it",
                      file=sys.stderr)
                continue
            if row.get("kind") == "meta":
                meta = row["meta"]
            elif row.get("kind") == "run":
                cp._runs.setdefault((row["task"], row["phase"], row["cell"]), []).append(row["result"])
        return cp, meta


def _probe_stdin(argv: list[str]) -> int:
    """E26: does `claude -p` take a prompt longer than the Windows command
    line cap intact from stdin? One call at sonnet/low, uncapped (a 0.25 cap aborted it, E26):
    a 40,000-character filler ending in an instruction to reply with one
    word that appears nowhere else in the prompt, so the reply proves the
    tail of the stdin prompt arrived, and a non-ASCII character in the
    filler so the encoding round-trips too."""
    import argparse
    ap = argparse.ArgumentParser(description="probe whether claude -p reads a long prompt from stdin (E26)")
    ap.add_argument("--project", type=Path, required=True, help="directory to run in")
    args = ap.parse_args(argv)
    filler = ("The following is filler text for a transport check; ignore its content. " * 500)[:39900]
    prompt = filler + " Ignore everything above (it is filler, including this em dash: \u2014). Reply with exactly the word PONG and nothing else."
    assert len(prompt) > STDIN_PROMPT_THRESHOLD_CHARS, len(prompt)
    res = call_claude(prompt, cwd=args.project, model="sonnet", effort="low", timeout=120)
    print(f"prompt {len(prompt)} chars via stdin; reply {res.result!r}; cost USD {res.cost_usd}; "
          f"extras {res.extras}; cmd {res.cmd_shown}")
    # The word only exists on the prompt's last line, so its presence in the
    # reply, quoted or obeyed, shows the tail arrived (a low-effort sonnet
    # declined the instruction as an injection and quoted it, E26).
    ok = "PONG" in res.result.upper()
    print("E26:", "PASS, the reply shows the prompt's last line arrived" if ok else "FAIL, the reply never mentions PONG")
    return 0 if ok else 1


if __name__ == "__main__":
    if sys.argv[1:2] == ["--probe-stdin"]:
        sys.exit(_probe_stdin(sys.argv[2:]))
    print(__doc__.splitlines()[0])
    print("usage: python3 tools/claudep.py --probe-stdin --project <dir>")
