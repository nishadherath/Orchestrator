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
import itertools
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


def load_route():
    """Import tools/route.py the same way load_generator() imports its sibling."""
    spec = importlib.util.spec_from_file_location("route", REPO_ROOT / "tools" / "route.py")
    assert spec and spec.loader, "cannot load tools/route.py"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_routing(r: Report, defs: dict[str, dict[str, str]]) -> None:
    routing = (SRC / "ROUTING.md").read_text(encoding="utf-8")
    gen = load_generator()
    named = set(gen.routing_assessments(gen.load_routing_table()))
    unknown = sorted(named - set(defs))
    r.add("ROUTE", "every worker named in src/routing_table.json has a definition", not unknown,
          f"{len(named)} names resolve" if not unknown else f"unresolved: {unknown}")
    unrouted = sorted(set(defs) - named)
    mislabelled = [n for n in unrouted if "Not in the routing table" not in defs[n].get("description", "")]
    r.add("ROUTE-DESC", "unrouted cells say so in their description", not mislabelled,
          f"{len(unrouted)} unrouted cells labelled" if not mislabelled else f"unlabelled: {mislabelled}")
    r.add("INV2", "Invariant 2: orchestrator never passes model on spawn",
          "Never pass a `model` parameter" in routing and all("never pass a model parameter" in d.get("description", "") for d in defs.values()),
          "ROUTING.md section 3 states it and every description repeats it. Whether an orchestrator obeys is measured by score_routing.py")


def _fixture_rows() -> list[dict]:
    """Every fixture with a confirmed assessment triple, as parsed rows.

    self_directed and prior_failure default to (False, "none") for a fixture
    that predates them, matching route.resolve()'s own defaults, though every
    fixture has carried both explicitly since D39 (docs/DECISIONS.md).
    """
    out: list[dict] = []
    if not FIXTURES.exists():
        return out
    for line in FIXTURES.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue  # check_fixtures reports malformed lines
        a = row.get("assessment")
        if not a or not row.get("expected_cell"):
            continue
        out.append({
            "id": row.get("id", "?"),
            "sensitivity": a.get("sensitivity"), "horizon": a.get("horizon"), "blast": a.get("blast"),
            "self_directed": row.get("self_directed", False), "prior_failure": row.get("prior_failure", "none"),
            "expected_cell": row["expected_cell"], "also_acceptable": row.get("also_acceptable", []),
        })
    return out


def check_row_backed(r: Report) -> None:
    """Every routing rule must be justified by a fixture that lands on it (D13).

    Measured 2026-09-06: a row with no fixture behind it does not merely sit
    unused, it changes how tasks are assessed and can pull correct answers off
    other rows. D9's "Mechanical, long horizon" row had no backing fixture and
    cost two fixtures that were correct before it existed. This check is that
    lesson made mechanical. Since D39 the table is data (src/routing_table.json)
    and "backed" is asked of each non-escalation rule directly, rather than by
    re-deriving triples from ROUTING.md's prose.
    """
    route_lib = load_route()
    table = route_lib.load_table()
    fixtures = _fixture_rows()
    unbacked_rules: list[str] = []
    for rule in table["rules"]:
        if rule.get("escalation_only"):
            continue  # the frontier row; no assessment triple backs a "prior failure" fact
        names = {rule["worker"], *rule.get("also_acceptable", [])}
        backed = any(
            f["expected_cell"] in names
            and route_lib.matching_rules(f["sensitivity"], f["horizon"], f["blast"],
                                          f["self_directed"], f["prior_failure"], table)[:1] == [rule]
            for f in fixtures
        )
        if not backed:
            unbacked_rules.append(rule["id"])
    covered_ids = [rule["id"] for rule in table["rules"] if not rule.get("escalation_only")]
    detail = (f"{len(covered_ids)} rules, {len(covered_ids) - len(unbacked_rules)} fixture-backed, "
              f"{len(unbacked_rules)} unbacked") if not unbacked_rules else \
             f"rules with no fixture landing on them: {unbacked_rules}"
    r.add("ROW-BACKED", "every routing rule is justified by a fixture whose confirmed answer lands on it",
          not unbacked_rules, detail)


def check_route_total(r: Report) -> None:
    """Every (sensitivity, horizon, blast) triple resolves to a worker, or a
    documented gap; and no two rules silently overlap outside the one
    disambiguation D39 documents (self_directed within open, long,
    consequential). Reads src/routing_table.json via tools/route.py rather
    than parsing ROUTING.md's prose.
    """
    route_lib = load_route()
    table = route_lib.load_table()
    decisions = (REPO_ROOT / "docs" / "DECISIONS.md").read_text(encoding="utf-8")
    universe = list(itertools.product(SENSITIVITY, HORIZON, BLAST))

    problems: list[str] = []
    documented_gaps = 0
    documented_overlaps = table.get("documented_overlaps", [])
    for s, h, b in universe:
        for self_directed in (False, True):
            matches = [m for m in route_lib.matching_rules(s, h, b, self_directed, "none", table)
                       if not m.get("escalation_only")]
            if not matches:
                if self_directed:
                    continue  # a gap is a property of the triple; self_directed=False already reported it
                reason = None
                for gap in table.get("documented_gaps", []):
                    gc = gap["conditions"]
                    if (gc["sensitivity"], gc["horizon"], gc["blast"]) == (s, h, b):
                        reason = gap["reason"]
                        break
                if reason and reason in decisions:
                    documented_gaps += 1
                elif reason:
                    problems.append(f"({s}, {h}, {b}) is a documented gap but its argument is missing from DECISIONS.md")
                else:
                    problems.append(f"no rule covers ({s}, {h}, {b})")
                continue
            if len(matches) == 1:
                continue
            ids = {m["id"] for m in matches}
            allowed = next((o for o in documented_overlaps
                            if {o["winner"], o["loser"]} == ids), None)
            if allowed and matches[0]["id"] == allowed["winner"]:
                continue
            problems.append(f"({s}, {h}, {b}, self_directed={self_directed}) matches {sorted(ids)} "
                             f"with no documented, correctly-ordered overlap")

    r.add("ROUTE-TOTAL", "every (sensitivity, horizon, blast) triple resolves to one worker, with self_directed "
          "disambiguating rather than conflicting", not problems,
          f"{len(universe)} triples, {documented_gaps} documented gap(s), "
          f"{len(documented_overlaps)} documented overlap(s)" if not problems else "; ".join(problems))


# The clarify rule's load-bearing sentences (D10). If the section is deleted or
# its two conditions are reworded away, score_routing.py keeps scoring an action
# the rubric no longer defines, which is the state D7 was raised to end.
CLARIFY_REQUIRED = (
    "### 1.1 Ask or route",
    "**No discoverable objective.**",
    "**Irreversible and materially ambiguous.**",
)


def check_table_data(r: Report) -> None:
    """Every fixture's recorded assessment resolves, through tools/route.py,
    to that fixture's own expected_cell or an also_acceptable value (D39,
    docs/DECISIONS.md; docs/CLASSIFIER-DESIGN.md). Deterministic and free,
    replacing a class of drift that previously showed up only in a paid
    score_routing.py run, or not at all: pre-flighting this exact check
    against the three-axis table alone is what surfaced that the table has
    five inputs, not three.
    """
    route_lib = load_route()
    table = route_lib.load_table()
    fixtures = _fixture_rows()
    mismatches: list[str] = []
    for f in fixtures:
        try:
            rule = route_lib.resolve(f["sensitivity"], f["horizon"], f["blast"],
                                      f["self_directed"], f["prior_failure"], table)
            got = rule["worker"]
        except route_lib.NoRuleMatches as exc:
            got = f"[gap: {exc}]"
        if got != f["expected_cell"] and got not in f["also_acceptable"]:
            mismatches.append(f"{f['id']}: table gives {got}, fixture expects {f['expected_cell']}")
    r.add("TABLE-DATA", "every fixture's assessment resolves through route.py to its expected cell",
          not mismatches, f"{len(fixtures)} fixtures checked" if not mismatches else "; ".join(mismatches))


def check_clarify(r: Report) -> None:
    routing = (SRC / "ROUTING.md").read_text(encoding="utf-8")
    missing = [s for s in CLARIFY_REQUIRED if s not in routing]
    exercised = 0
    if FIXTURES.exists():
        for line in FIXTURES.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                if json.loads(line).get("expected_action") == "clarify":
                    exercised += 1
            except json.JSONDecodeError:
                continue  # malformed lines are check_fixtures' report, not this one
    problems: list[str] = []
    if missing:
        problems.append(f"ROUTING.md is missing {missing}")
    if not exercised:
        problems.append("no fixture sets expected_action clarify, so the rule is never exercised")
    r.add("CLARIFY", "the clarify rule is stated in ROUTING.md and at least one fixture exercises it",
          not problems,
          f"rule present with both conditions, {exercised} clarify fixture" if not problems else "; ".join(problems))


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
            if EM_DASH in line and not _is_relayed_line(line):
                problems.append(f"{rel}:{n}: em-dash")
            stripped = URL_RE.sub("", CODE_SPAN_RE.sub("", line))
            low = stripped.lower()
            for w in BANNED_WORDS:
                if re.search(rf"\b{w}\b", low) and not _is_definition_line(rel, line) and not _is_relayed_line(line):
                    problems.append(f"{rel}:{n}: banned word {w!r}")
            for ph in BANNED_PHRASES:
                if ph in low and not _is_definition_line(rel, line) and not _is_relayed_line(line):
                    problems.append(f"{rel}:{n}: banned phrase {ph!r}")
            for pat in US_SPELLINGS:
                if re.search(pat, stripped, flags=re.IGNORECASE) and not _is_definition_line(rel, line) and not _is_relayed_line(line):
                    problems.append(f"{rel}:{n}: US spelling matches {pat!r}")
    r.add("PROSE", "no em-dash, banned words, US spelling, CR, or missing final newline in authored files",
          not problems, f"{len(prose_files())} files clean" if not problems else "; ".join(problems[:12]))


def _is_definition_line(rel: Path, line: str) -> bool:
    """The harness and the persona list the banned terms; those lines are exempt."""
    return rel.name == "check.py" and ("BANNED" in line or "US_SPELLINGS" in line or line.lstrip().startswith("r\""))


def _is_relayed_line(line: str) -> bool:
    """A line carrying a worker's or grader's own words, quoted verbatim by
    benchmark.py's render(), is not authored prose and is exempt from the
    style checks below (D36, docs/DECISIONS.md; the exemption a6b7426's
    commit message flagged as a pending decision and left unresolved).
    Rewriting a worker's exact words to pass a style check would corrupt
    the evidentiary record; detected by the literal "grader: " / "worker: "
    markers render() inserts, not by file name, so authored text sharing a
    result file with relayed text stays checked.

    A line that is one JSON record (starts with the record-type key and
    ends with a closing brace) is also relayed: tools/role_probe.py and the
    Stage 10 Controller reproduce a role's records verbatim in result
    files, and a record's field text is the model's words, not authored
    prose. Records in test/fixtures/system/ are authored and would be
    caught by this exemption too; they are kept to the house style by
    hand, since the fixture emitter is not a model."""
    stripped = line.strip()
    return ("grader: " in line or " || worker: " in line
            or (stripped.startswith('{"type": "') and stripped.endswith("}")))


def check_persona_manifest(r: Report, update: bool) -> None:
    # Paths are normalised to POSIX form (forward slashes) on both the write
    # and read sides so the manifest compares equal on Windows and Linux;
    # str(Path) yields backslashes on Windows, which made every entry here
    # register as changed on a Windows run even with identical content.
    files = persona_files()
    current = {p.relative_to(REPO_ROOT).as_posix(): cr_stripped_sha256(p) for p in files}
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
        recorded[name.replace("\\", "/")] = digest
    changed = sorted(n for n in current if recorded.get(n) != current[n])
    missing = sorted(set(recorded) - set(current))
    extra = sorted(set(current) - set(recorded))
    ok = not (changed or missing or extra)
    r.add("PERSONA", "generated persona files unchanged since manifest", ok,
          f"{len(current)} files match" if ok else f"changed={changed} missing={missing} unlisted={extra}; rebuild from source, do not hand-edit (DECISIONS.md D2)")


SYSTEM_FIXTURES = REPO_ROOT / "test" / "fixtures" / "system"
# The line numbers in broken.jsonl that carry a deliberate defect. The check
# asserts the validator reports exactly these and no others, so a validator
# that goes blind to one defect class, or starts rejecting sound records,
# fails here rather than in a Stage 10 run.
BROKEN_LINES = {1, 2, 3, 5, 6, 10, 13, 16, 17, 18}


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_records", REPO_ROOT / "tools" / "validate_records.py")
    assert spec and spec.loader, "cannot load tools/validate_records.py"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_schemas(r: Report) -> None:
    """SCHEMA: every record type has a schema, valid.jsonl validates clean,
    and broken.jsonl is rejected on exactly the documented lines (Stage 9.3)."""
    valid = SYSTEM_FIXTURES / "valid.jsonl"
    broken = SYSTEM_FIXTURES / "broken.jsonl"
    if not valid.exists() or not broken.exists():
        r.add("SCHEMA", "record schemas validate the example ledgers", False,
              f"{SYSTEM_FIXTURES.relative_to(REPO_ROOT)} needs valid.jsonl and broken.jsonl")
        return
    try:
        v = load_validator()
        schemas = v.load_schemas()
    except Exception as exc:
        r.add("SCHEMA", "record schemas validate the example ledgers", False, f"validator failed to load: {exc}")
        return
    problems: list[str] = []
    expected_types = {"ProblemRecord", "PremiseRecord", "FrameRecord", "MeasurementRecord", "CandidateRecord",
                      "CritiqueRecord", "SelectionRecord", "EvaluationRecord", "SolutionRecord", "GapReport",
                      "PhaseDigest", "BudgetEntry"}
    missing = expected_types - set(schemas)
    if missing:
        problems.append(f"no schema for {sorted(missing)}")

    records, parse = v.read_jsonl([valid])
    found = v.validate_ledger(records, schemas, strict=True) + parse
    if found:
        problems.append(f"valid.jsonl: {len(found)} problem(s), first: {found[0]}")
    types_seen = {rec.get("type") for _, rec in records if isinstance(rec, dict)}
    if expected_types - types_seen:
        problems.append(f"valid.jsonl lacks an example of {sorted(expected_types - types_seen)}")

    records, parse = v.read_jsonl([broken])
    found = v.validate_ledger(records, schemas, strict=True) + parse
    lines = set()
    for msg in found:
        head = msg.split(": ", 1)[0]
        try:
            lines.add(int(head.rsplit(":", 1)[1]))
        except (IndexError, ValueError):
            problems.append(f"unparseable validator message: {msg}")
    if lines != BROKEN_LINES:
        problems.append(f"broken.jsonl rejected on lines {sorted(lines)}, expected {sorted(BROKEN_LINES)}")

    r.add("SCHEMA", "record schemas validate the example ledgers", not problems,
          f"{len(schemas)} schemas; valid.jsonl clean; broken.jsonl rejected on {len(BROKEN_LINES)} documented lines"
          if not problems else "; ".join(problems))


def check_system_controller(r: Report) -> None:
    """SYSTEM: tools/system_controller.py's --selftest passes: eleven scripted
    scenarios (a pretty-printed-record parse plus nested-schema surfacing,
    happy path, dissolution, budget exhaustion, stale-version rejection,
    single-writer rejection, reframe cap, reframed-continues, self-chosen-id
    remap, non-Frame retry recovery, a runner out of budget closing as a
    gap), no claude -p calls (docs/PLAN.md Stage 10.6; scenarios 0, 7, 8, 9
    and 10 added after live runs in Stages 10.9 and 11.3 found real bugs)."""
    script = REPO_ROOT / "tools" / "system_controller.py"
    if not script.exists():
        r.add("SYSTEM", "system_controller.py --selftest passes", False, f"{script.relative_to(REPO_ROOT)} missing")
        return
    proc = subprocess.run([sys.executable, str(script), "--selftest"], capture_output=True, text=True, timeout=60)
    r.add("SYSTEM", "system_controller.py --selftest passes", proc.returncode == 0,
          proc.stdout.strip().splitlines()[-1] if proc.returncode == 0 else (proc.stdout + proc.stderr).strip()[-800:])


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
            if not isinstance(row.get("self_directed"), bool):
                problems.append(f"{fid}: self_directed missing or not a bool: {row.get('self_directed')!r}")
            if row.get("prior_failure") not in ("none", "failed_at_xhigh"):
                problems.append(f"{fid}: prior_failure outside vocabulary: {row.get('prior_failure')!r}")
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
    check_route_total(report)
    check_row_backed(report)
    check_table_data(report)
    check_clarify(report)
    check_environment(report)
    check_available_models(report)
    check_invariant7(report)
    check_prose(report)
    check_persona_manifest(report, args.update_persona_manifest)
    check_fixtures(report, defs)
    check_schemas(report)
    check_system_controller(report)

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
