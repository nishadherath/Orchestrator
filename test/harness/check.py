#!/usr/bin/env python3
"""Regression harness: one assertion per CLAUDE.md invariant, plus artefact checks.

Responsible for: everything about this repository that can be checked without
a live Claude Code session. Each check reports PASS, FAIL or SKIP with a
reason. A SKIP is an invariant that needs the empirical checklist; it is
never silently counted as a pass. Exit status is 1 if any check FAILs.

Deliberately does not: run Claude Code, spawn workers, or judge routing
appropriateness. Those need `empirical-checklist.md` and `score_routing.py`.

The one non-obvious thing: the environment checks (INV1, INV3, INV4) assert
the environment the harness runs in, which is only meaningful when that is
the environment a dogfooding session will start from. Run it from the same
shell.

Usage:
    python3 test/harness/check.py                       human-readable
    python3 test/harness/check.py --json                machine-readable
    python3 test/harness/check.py --record              also write test/results/<date>-harness.md
    python3 test/harness/check.py --update-persona-manifest
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import importlib.util
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR = REPO_ROOT / "tools" / "generate_workers.py"
SRC = REPO_ROOT / "src"
AGENTS_DIR = SRC / "agents"
FIXTURES = REPO_ROOT / "test" / "fixtures" / "routing.jsonl"
RESULTS_DIR = REPO_ROOT / "test" / "results"
PERSONA_MANIFEST = REPO_ROOT / "test" / "harness" / "persona.sha256"

# tools/ is put on sys.path so `cells` resolves when this file runs as a script.
sys.path.insert(0, str(REPO_ROOT / "tools"))
from cells import MODELS, EFFORTS  # noqa: E402 (path must be set first)

SENSITIVITY = ("mechanical", "structured", "open")
HORIZON = ("short", "medium", "long")
BLAST = ("contained", "consequential")

EM_DASH = "\u2014"
BANNED_WORDS = ("delve", "nuanced", "tapestry", "robust", "multifaceted", "landscape")
BANNED_PHRASES = ("it is worth noting", "it is important to note", "let's dive in", "in today's world")
US_SPELLINGS = (r"optimiz", r"analyz", r"\bbehaviors?\b", r"recogniz", r"organiz", r"\bcolors?\b",
                r"\bcenter\b", r"\bcatalog\b", r"\bfavor\b", r"\bmodeling\b", r"\bsignaling\b")
CODE_SPAN_RE = re.compile(r"`[^`\n]*`")
URL_RE = re.compile(r"https?://\S+")

# Prose-checked files: everything this repository authors. Generated persona
# files are guarded by hash instead (D2) and are excluded here.
PROSE_GLOBS = ("CLAUDE.md", "src/**/*.md", "src/*.py", "docs/*.md", "test/**/*.md", "tools/*.py", "test/harness/*.py")


@dataclass
class Check:
    id: str
    covers: str
    status: str  # PASS | FAIL | SKIP
    detail: str


@dataclass
class Report:
    checks: list[Check] = field(default_factory=list)

    def add(self, id_: str, covers: str, ok: bool | None, detail: str) -> None:
        status = "SKIP" if ok is None else ("PASS" if ok else "FAIL")
        self.checks.append(Check(id_, covers, status, detail))

    @property
    def failed(self) -> int:
        return sum(1 for c in self.checks if c.status == "FAIL")


# ---------------------------------------------------------------- helpers

def parse_frontmatter(text: str) -> dict[str, str]:
    assert text.startswith("---\n"), "definition does not start with frontmatter"
    end = text.index("\n---\n", 4)
    out: dict[str, str] = {}
    for line in text[4:end].splitlines():
        key, _, value = line.partition(":")
        out[key.strip()] = value.strip()
    return out


def prose_files() -> list[Path]:
    files: set[Path] = set()
    for pattern in PROSE_GLOBS:
        files.update(p for p in REPO_ROOT.glob(pattern) if p.is_file())
    return sorted(files)


def persona_files() -> list[Path]:
    files = sorted(REPO_ROOT.glob("ENGINEERING_PERSONA.*.md"))
    files += sorted((REPO_ROOT / "ENGINEERING_PERSONA_LANGUAGES").glob("*.md"))
    return files


def cr_stripped_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r", b"")).hexdigest()


def env_state(name: str) -> str:
    value = os.environ.get(name)
    return "unset" if value is None else f"set to {value!r}"


# ----------------------------------------------------------------- checks

def check_definitions(r: Report) -> dict[str, dict[str, str]]:
    defs: dict[str, dict[str, str]] = {}
    problems: list[str] = []
    files = sorted(AGENTS_DIR.glob("*.md"))
    for path in files:
        try:
            fm = parse_frontmatter(path.read_text(encoding="utf-8"))
        except (AssertionError, ValueError) as exc:
            problems.append(f"{path.name}: {exc}")
            continue
        expected_name = f"worker-{fm.get('model')}-{fm.get('effort')}"
        expected_file = f"WORKER_{fm.get('model')}_{fm.get('effort')}.md"
        if fm.get("name") != expected_name:
            problems.append(f"{path.name}: name {fm.get('name')!r} != {expected_name!r}")
        if path.name != expected_file:
            problems.append(f"{path.name}: filename does not match {expected_file}")
        if fm.get("model") not in MODELS:
            problems.append(f"{path.name}: model {fm.get('model')!r} outside {MODELS}")
        if fm.get("effort") not in EFFORTS:
            problems.append(f"{path.name}: effort {fm.get('effort')!r} outside {EFFORTS}")
        if not fm.get("description"):
            problems.append(f"{path.name}: empty description")
        defs[fm.get("name", path.name)] = fm
    expected = {f"worker-{m}-{e}" for m in MODELS for e in EFFORTS}
    missing = expected - set(defs)
    extra = set(defs) - expected
    if missing:
        problems.append(f"missing cells: {sorted(missing)}")
    if extra:
        problems.append(f"cells outside the matrix: {sorted(extra)}")
    r.add("DEF", "15 definitions parse and match the 3x5 matrix", not problems,
          f"{len(files)} files" if not problems else "; ".join(problems))
    r.add("INV5", "Invariant 5: no haiku cell", all(d.get("model") != "haiku" for d in defs.values()),
          "no definition sets model: haiku. The original justification (haiku lacks effort levels) was "
          "disproved empirically 2026-09-05 (FINDINGS.md); the exclusion itself is a decision, not a gap "
          "(DECISIONS.md D5, 2026-09-05).")
    return defs


def check_generator(r: Report) -> None:
    proc = subprocess.run([sys.executable, str(REPO_ROOT / "tools" / "generate_workers.py"), "--check", "--json"],
                          capture_output=True, text=True, cwd=REPO_ROOT)
    if proc.returncode not in (0, 1):
        r.add("GEN", "src/agents/ matches the generator output", False, f"generator crashed: {proc.stderr.strip()[-300:]}")
        return
    data = json.loads(proc.stdout)
    drifted = [f["file"] for f in data["files"] if f["status"] != "unchanged"]
    r.add("GEN", "src/agents/ matches the generator output", not drifted,
          "no drift" if not drifted else f"drifted: {drifted}; run python3 tools/generate_workers.py")


def load_generator():
    """Import tools/generate_workers.py so the harness shares its table parser."""
    spec = importlib.util.spec_from_file_location("generate_workers", GENERATOR)
    assert spec and spec.loader, f"cannot load {GENERATOR}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_routing(r: Report, defs: dict[str, dict[str, str]]) -> None:
    routing = (SRC / "ROUTING.md").read_text(encoding="utf-8")
    named = set(load_generator().routing_assessments(routing))
    unknown = sorted(named - set(defs))
    r.add("ROUTE", "every worker named in ROUTING.md has a definition", not unknown,
          f"{len(named)} names resolve" if not unknown else f"unresolved: {unknown}")
    unrouted = sorted(set(defs) - named)
    mislabelled = [n for n in unrouted if "Not in the routing table" not in defs[n].get("description", "")]
    r.add("ROUTE-DESC", "unrouted cells say so in their description", not mislabelled,
          f"{len(unrouted)} unrouted cells labelled" if not mislabelled else f"unlabelled: {mislabelled}")
    r.add("INV2", "Invariant 2: orchestrator never passes model on spawn",
          "Never pass a `model` parameter" in routing and all("never pass a model parameter" in d.get("description", "") for d in defs.values()),
          "ROUTING.md section 3 states it and every description repeats it. Whether an orchestrator obeys is measured by score_routing.py")


def check_environment(r: Report) -> None:
    teams = os.environ.get("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS")
    r.add("INV1", "Invariant 1: agent teams off so effort is per-worker", teams in (None, "", "0"),
          f"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS {env_state('CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS')}")
    r.add("INV3", "Invariant 3: session effort override unset", "CLAUDE_CODE_EFFORT_LEVEL" not in os.environ,
          f"CLAUDE_CODE_EFFORT_LEVEL {env_state('CLAUDE_CODE_EFFORT_LEVEL')}")
    force = os.environ.get("CLAUDE_CODE_SUBAGENT_MODEL_FORCE")
    default_model = os.environ.get("CLAUDE_CODE_SUBAGENT_MODEL")
    r.add("INV4", "Invariant 4: subagent model force off", force in (None, "", "0") and default_model is None,
          f"CLAUDE_CODE_SUBAGENT_MODEL_FORCE {env_state('CLAUDE_CODE_SUBAGENT_MODEL_FORCE')}; "
          f"CLAUDE_CODE_SUBAGENT_MODEL {env_state('CLAUDE_CODE_SUBAGENT_MODEL')}")


def check_available_models(r: Report) -> None:
    candidates = [Path.home() / ".claude" / "settings.json",
                  REPO_ROOT / ".claude" / "settings.json",
                  REPO_ROOT / ".claude" / "settings.local.json"]
    found: list[str] = []
    blocked: list[str] = []
    for path in candidates:
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            blocked.append(f"{path}: unparseable ({exc})")
            continue
        allow = data.get("availableModels")
        if allow is None:
            continue
        found.append(str(path))
        allow_text = json.dumps(allow).lower()
        for model in MODELS:
            if model not in allow_text:
                blocked.append(f"{path}: availableModels does not mention {model}")
    if not found and not blocked:
        r.add("INV6", "Invariant 6: availableModels permits all three models", True,
              f"no availableModels allowlist in {[str(c) for c in candidates if c.exists()] or 'any checked settings file'}; substitution cannot occur from these files. Managed enterprise settings are not checked here")
    else:
        r.add("INV6", "Invariant 6: availableModels permits all three models", not blocked,
              f"allowlist in {found}" if not blocked else "; ".join(blocked))


def check_invariant7(r: Report) -> None:
    r.add("INV7", "Invariant 7: user-stopped worker is not resumable", None,
          "needs a live session: empirical-checklist.md items E3 and E4")


def check_prose(r: Report) -> None:
    problems: list[str] = []
    for path in prose_files():
        raw = path.read_bytes()
        rel = path.relative_to(REPO_ROOT)
        if b"\r" in raw:
            problems.append(f"{rel}: CR found")
        if not raw.endswith(b"\n"):
            problems.append(f"{rel}: no trailing newline")
        text = raw.decode("utf-8")
        for n, line in enumerate(text.splitlines(), 1):
            if EM_DASH in line:
                problems.append(f"{rel}:{n}: em-dash")
            stripped = URL_RE.sub("", CODE_SPAN_RE.sub("", line))
            low = stripped.lower()
            for w in BANNED_WORDS:
                if re.search(rf"\b{w}\b", low) and not _is_definition_line(rel, line):
                    problems.append(f"{rel}:{n}: banned word {w!r}")
            for ph in BANNED_PHRASES:
                if ph in low and not _is_definition_line(rel, line):
                    problems.append(f"{rel}:{n}: banned phrase {ph!r}")
            for pat in US_SPELLINGS:
                if re.search(pat, stripped, flags=re.IGNORECASE) and not _is_definition_line(rel, line):
                    problems.append(f"{rel}:{n}: US spelling matches {pat!r}")
    r.add("PROSE", "no em-dash, banned words, US spelling, CR, or missing final newline in authored files",
          not problems, f"{len(prose_files())} files clean" if not problems else "; ".join(problems[:12]))


def _is_definition_line(rel: Path, line: str) -> bool:
    """The harness and the persona list the banned terms; those lines are exempt."""
    return rel.name == "check.py" and ("BANNED" in line or "US_SPELLINGS" in line or line.lstrip().startswith("r\""))


def check_persona_manifest(r: Report, update: bool) -> None:
    files = persona_files()
    current = {str(p.relative_to(REPO_ROOT)): cr_stripped_sha256(p) for p in files}
    if update:
        with PERSONA_MANIFEST.open("w", encoding="utf-8", newline="\n") as fh:
            for name, digest in sorted(current.items()):
                fh.write(f"{digest}  {name}\n")
        r.add("PERSONA", "generated persona files unchanged since manifest", True, f"manifest rewritten with {len(current)} entries")
        return
    if not PERSONA_MANIFEST.exists():
        r.add("PERSONA", "generated persona files unchanged since manifest", False,
              "no manifest; run with --update-persona-manifest after confirming the files came from the builder")
        return
    recorded: dict[str, str] = {}
    for line in PERSONA_MANIFEST.read_text(encoding="utf-8").splitlines():
        digest, _, name = line.partition("  ")
        recorded[name] = digest
    changed = sorted(n for n in current if recorded.get(n) != current[n])
    missing = sorted(set(recorded) - set(current))
    extra = sorted(set(current) - set(recorded))
    ok = not (changed or missing or extra)
    r.add("PERSONA", "generated persona files unchanged since manifest", ok,
          f"{len(current)} files match" if ok else f"changed={changed} missing={missing} unlisted={extra}; rebuild from source, do not hand-edit (DECISIONS.md D2)")


def check_fixtures(r: Report, defs: dict[str, dict[str, str]]) -> None:
    if not FIXTURES.exists():
        r.add("FIX", "routing fixtures are well-formed", False, f"{FIXTURES.relative_to(REPO_ROOT)} missing")
        return
    problems: list[str] = []
    ids: set[str] = set()
    rows = 0
    for n, line in enumerate(FIXTURES.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        rows += 1
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            problems.append(f"line {n}: {exc}")
            continue
        fid = row.get("id", "")
        if not re.fullmatch(r"F\d\d", fid) or fid in ids:
            problems.append(f"line {n}: bad or duplicate id {fid!r}")
        ids.add(fid)
        for key in ("task", "rationale", "assigned_by"):
            if not row.get(key):
                problems.append(f"{fid}: missing {key}")
        if row.get("expected_action"):
            if row.get("expected_cell") is not None:
                problems.append(f"{fid}: expected_action with a non-null expected_cell")
        else:
            a = row.get("assessment") or {}
            if a.get("sensitivity") not in SENSITIVITY or a.get("horizon") not in HORIZON or a.get("blast") not in BLAST:
                problems.append(f"{fid}: assessment outside vocabulary: {a}")
            for cell in [row.get("expected_cell")] + list(row.get("also_acceptable", [])):
                if cell not in defs:
                    problems.append(f"{fid}: unknown cell {cell!r}")
    r.add("FIX", "routing fixtures are well-formed", not problems,
          f"{rows} fixtures, {len(ids)} ids" if not problems else "; ".join(problems[:8]))


# ------------------------------------------------------------------- main

def render_markdown(report: Report, when: dt.datetime, git_rev: str) -> str:
    lines = [f"# Harness run {when.strftime('%Y-%m-%d %H:%M')} at {git_rev}", "",
             f"Result: {'PASS' if report.failed == 0 else 'FAIL'} "
             f"({sum(c.status == 'PASS' for c in report.checks)} pass, {report.failed} fail, "
             f"{sum(c.status == 'SKIP' for c in report.checks)} skip)", "",
             "| Check | Covers | Status | Detail |", "| :--- | :--- | :--- | :--- |"]
    for c in report.checks:
        lines.append(f"| {c.id} | {c.covers} | {c.status} | {c.detail.replace('|', '/')} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--record", action="store_true", help="write test/results/<date>-harness.md")
    ap.add_argument("--update-persona-manifest", action="store_true")
    args = ap.parse_args(argv)

    report = Report()
    defs = check_definitions(report)
    check_generator(report)
    check_routing(report, defs)
    check_environment(report)
    check_available_models(report)
    check_invariant7(report)
    check_prose(report)
    check_persona_manifest(report, args.update_persona_manifest)
    check_fixtures(report, defs)

    when = dt.datetime.now()
    try:
        git_rev = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=REPO_ROOT).stdout.strip() or "no-git"
    except OSError:
        git_rev = "no-git"

    if args.json:
        print(json.dumps({"result": "PASS" if report.failed == 0 else "FAIL", "git": git_rev,
                          "checks": [c.__dict__ for c in report.checks]}, indent=2))
    else:
        for c in report.checks:
            print(f"{c.status:4}  {c.id:<10} {c.covers}\n      {c.detail}")
        print(f"\n{'PASS' if report.failed == 0 else 'FAIL'}: {report.failed} failing of {len(report.checks)} checks at {git_rev}")
    if args.record:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        out = RESULTS_DIR / f"{when.strftime('%Y-%m-%d')}-harness.md"
        out.write_text(render_markdown(report, when, git_rev), encoding="utf-8", newline="\n")
        print(f"recorded {out.relative_to(REPO_ROOT)}")
    return 1 if report.failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
