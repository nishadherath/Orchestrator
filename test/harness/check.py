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
SETTINGS_FRAGMENT = SRC / "settings.fragment.json"
FINDINGS = REPO_ROOT / "docs" / "FINDINGS.md"
DIST = REPO_ROOT / "dist"

# tools/ is put on sys.path so `cells` resolves when this file runs as a script.
sys.path.insert(0, str(REPO_ROOT / "tools"))
from cells import MODELS, EFFORTS  # noqa: E402 (path must be set first)
from route import _atomic_write_bytes  # noqa: E402

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
# files are guarded by hash instead (D2) and are excluded here. README.md
# added 2026-09-16 (docs/PLAN-6.md D.2, audit A3): the root orientation
# document was unguarded by this check, the same gap USAGE_PROJECT.md had
# before B.1 deleted it.
PROSE_GLOBS = ("CLAUDE.md", "README.md", "src/**/*.md", "src/*.py", "docs/*.md", "test/**/*.md", "tools/*.py", "test/harness/*.py", "handoffs/*.md")


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


def load_build_dist():
    """Import tools/build_dist.py the same way load_generator() imports its sibling."""
    spec = importlib.util.spec_from_file_location("build_dist", REPO_ROOT / "tools" / "build_dist.py")
    assert spec and spec.loader, "cannot load tools/build_dist.py"
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


ROUTE_PY_FLAG_RE = re.compile(r"--[a-z][a-z-]*")


def check_route_modes(r: Report) -> None:
    """ROUTE-MODES: every `route.py` flag named in a command
    `src/settings.fragment.json` wires up (a `statusLine`,
    `subagentStatusLine`, or hook command) is named somewhere in
    `src/ROUTING.md` or `src/LIFECYCLE.md`.

    Guards against the class of defect audit finding B1
    (`docs/AUDIT-2026-09-16.md`) found: `docs/COMPACTION-DESIGN.md`
    documented a `route.py --spawn` step it asserted `ROUTING.md`
    already had, and `ROUTING.md` never actually had it, so the
    `SessionStart(compact)` hook's pending-worker list was always
    empty in every consumer install. A mode the fragment wires up
    silently, with no shipped prose ever mentioning it, is exactly
    this failure and this check makes it fail loudly instead."""
    if not SETTINGS_FRAGMENT.exists():
        r.add("ROUTE-MODES", "every route.py flag the fragment wires up is named in the shipped prose",
              False, f"{SETTINGS_FRAGMENT.relative_to(REPO_ROOT)} missing")
        return
    try:
        fragment = json.loads(SETTINGS_FRAGMENT.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        r.add("ROUTE-MODES", "every route.py flag the fragment wires up is named in the shipped prose",
              False, f"{SETTINGS_FRAGMENT.relative_to(REPO_ROOT)}: invalid JSON: {exc}")
        return

    commands: list[str] = []
    for key in ("statusLine", "subagentStatusLine"):
        cmd = (fragment.get(key) or {}).get("command")
        if cmd:
            commands.append(cmd)
    for entry in (fragment.get("hooks", {}) or {}).get("SessionStart", []) or []:
        for hook in entry.get("hooks", []) or []:
            cmd = hook.get("command")
            if cmd:
                commands.append(cmd)

    flags: set[str] = set()
    for cmd in commands:
        if "route.py" not in cmd:
            continue
        flags.update(ROUTE_PY_FLAG_RE.findall(cmd))

    prose = ((SRC / "ROUTING.md").read_text(encoding="utf-8")
             + (SRC / "LIFECYCLE.md").read_text(encoding="utf-8"))
    missing = sorted(f for f in flags if f not in prose)
    r.add("ROUTE-MODES", "every route.py flag the fragment wires up is named in the shipped prose",
          not missing, f"{len(flags)} flag(s) checked, all named" if not missing
          else f"named in the fragment's commands but nowhere in ROUTING.md or LIFECYCLE.md: {missing}")


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
    "### 1.2 Ask or route",
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
    """PASS if docs/FINDINGS.md has a dated row citing E4 (the user-stop half
    of invariant 7); SKIP otherwise. Corrected 2026-09-16 (docs/PLAN-6.md
    D.2, audit A2, B8): this was a permanent SKIP naming E3 and E4 as
    still-needed, even after both were done and recorded (2026-09-05,
    re-verified 2026-09-11); it never read the file it was telling a
    session to check.
    """
    text = FINDINGS.read_text(encoding="utf-8") if FINDINGS.exists() else ""
    sections = re.split(r"(?m)^## ", text)[1:]  # drop the preamble before the first heading
    for section in sections:
        heading, _, body = section.partition("\n")
        date_m = re.search(r"\d{4}-\d{2}-\d{2}", heading)
        if date_m and re.search(r"\bE4\b", body):
            r.add("INV7", "Invariant 7: user-stopped worker is not resumable", True,
                  f"docs/FINDINGS.md, {date_m.group()} ({heading.strip()})")
            return
    r.add("INV7", "Invariant 7: user-stopped worker is not resumable", None,
          "needs a live session: empirical-checklist.md items E3 and E4; "
          "no dated E4 row found in docs/FINDINGS.md")


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


def check_dist(r: Report) -> None:
    """DIST: dist/ is faithful to what tools/build_dist.py would write at its
    own committed stamp (docs/PLAN-6.md D.2, audit C7). Every other
    generated artefact has a drift check (GEN for src/agents/, ROUTE-PRIORS
    for the priors, PERSONA for the personas); dist/ had none, so a dist/
    that was one source edit stale passed every other check. This is
    pass 1's own scratchpad script (docs/AUDIT-2026-09-16.md), made
    permanent: planned_files() is called with the stamp already committed
    in dist/.claude/ORCHESTRATOR_VERSION, not a freshly computed one (a
    fresh stamp differs on every run, by the commit hash alone, and would
    make this check FAIL on every clean checkout).
    """
    version_file = DIST / ".claude" / "ORCHESTRATOR_VERSION"
    if not version_file.exists():
        r.add("DIST", "dist/ matches build_dist.planned_files() at its committed stamp", False,
              f"{version_file.relative_to(REPO_ROOT)} missing; dist/ not built")
        return
    committed_version = version_file.read_text(encoding="utf-8").strip()
    build_dist = load_build_dist()
    with_rationale = committed_version.endswith("-with-rationale")
    planned = build_dist.planned_files(committed_version, DIST, with_rationale)
    on_disk = {p for p in DIST.rglob("*") if p.is_file()}
    problems: list[str] = []
    for path, content in planned.items():
        if not path.exists():
            problems.append(f"missing: {path.relative_to(REPO_ROOT)}")
        elif path.read_text(encoding="utf-8") != content:
            problems.append(f"changed: {path.relative_to(REPO_ROOT)}")
    extra = sorted(p for p in on_disk - set(planned))
    for path in extra:
        problems.append(f"unplanned: {path.relative_to(REPO_ROOT)}")
    ok = not problems
    r.add("DIST", "dist/ matches build_dist.planned_files() at its committed stamp", ok,
          f"{len(planned)} files match at {committed_version}" if ok
          else f"{len(problems)} problem(s) at {committed_version}: {problems[:10]}")


SYSTEM_FIXTURES = REPO_ROOT / "test" / "fixtures" / "system"
# The line numbers in broken.jsonl that carry a deliberate defect. The check
# asserts the validator reports exactly these and no others, so a validator
# that goes blind to one defect class, or starts rejecting sound records,
# fails here rather than in a Stage 10 run.
BROKEN_LINES = {1, 2, 3, 5, 6, 10, 13, 16, 17, 18, 19, 20}


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
                      "PhaseDigest", "BudgetEntry", "RoutingLedgerEntry"}
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
    """SYSTEM: tools/system_controller.py's --selftest passes: twelve scripted
    scenarios (a pretty-printed-record parse plus nested-schema surfacing,
    happy path, dissolution, budget exhaustion, stale-version rejection,
    single-writer rejection, reframe cap, reframed-continues, self-chosen-id
    remap, non-Frame retry recovery, a runner out of budget closing as a
    gap, a role's output that never converges closing as a gap), no
    claude -p calls (docs/PLAN.md Stage 10.6; scenarios 0, 7, 8, 9 and 10
    added after live runs in Stages 10.9 and 11.3 found real bugs;
    scenario 11 added by docs/PLAN-6.md Stage B.6, audit A15)."""
    script = REPO_ROOT / "tools" / "system_controller.py"
    if not script.exists():
        r.add("SYSTEM", "system_controller.py --selftest passes", False, f"{script.relative_to(REPO_ROOT)} missing")
        return
    proc = subprocess.run([sys.executable, str(script), "--selftest"], capture_output=True, text=True, timeout=60)
    r.add("SYSTEM", "system_controller.py --selftest passes", proc.returncode == 0,
          proc.stdout.strip().splitlines()[-1] if proc.returncode == 0 else (proc.stdout + proc.stderr).strip()[-800:])


def check_controller_routing_r0(r: Report) -> None:
    """CTRL-R0: future contracts are complete and inspected gaps remain
    executable characterisations until their named implementation stage."""
    tests = REPO_ROOT / "test" / "harness" / "controller_routing_r0_tests.py"
    proc = subprocess.run([sys.executable, str(tests)], cwd=REPO_ROOT,
                          capture_output=True, text=True, timeout=90)
    detail = (proc.stdout + proc.stderr).strip()
    r.add("CTRL-R0", "Controller routing contracts and baseline gaps are pinned",
          proc.returncode == 0,
          detail.splitlines()[-1] if proc.returncode == 0 else detail[-1200:])


def check_controller_integrity_r1(r: Report) -> None:
    """CTRL-R1: integrity-v1 adversarial tests pass without provider calls."""
    tests = REPO_ROOT / "test" / "harness" / "controller_integrity_tests.py"
    proc = subprocess.run([sys.executable, str(tests)], cwd=REPO_ROOT,
                          capture_output=True, text=True, timeout=90)
    detail = (proc.stdout + proc.stderr).strip()
    r.add("CTRL-R1", "Controller integrity-v1 gates and evidence packets hold",
          proc.returncode == 0,
          detail.splitlines()[-1] if proc.returncode == 0 else detail[-1600:])


def check_model_registry_r2(r: Report) -> None:
    """CTRL-R2: all fifteen cells and role profiles resolve offline."""
    tests = REPO_ROOT / "test" / "harness" / "model_registry_tests.py"
    proc = subprocess.run([sys.executable, str(tests)], cwd=REPO_ROOT,
                          capture_output=True, text=True, timeout=90)
    detail = (proc.stdout + proc.stderr).strip()
    r.add("CTRL-R2", "all 15 cells resolve with exact identity and unknown-cost handling",
          proc.returncode == 0,
          detail.splitlines()[-1] if proc.returncode == 0 else detail[-1600:])


def check_controller_control_r3(r: Report) -> None:
    """CTRL-R3: durable controls preserve precedence and process safety."""
    tests = REPO_ROOT / "test" / "harness" / "controller_control_tests.py"
    proc = subprocess.run([sys.executable, str(tests)], cwd=REPO_ROOT,
                          capture_output=True, text=True, timeout=90)
    detail = (proc.stdout + proc.stderr).strip()
    r.add("CTRL-R3", "durable auto/on/off controls are atomic, scoped and provider-free",
          proc.returncode == 0,
          detail.splitlines()[-1] if proc.returncode == 0 else detail[-1600:])


def check_controller_routing_r4(r: Report) -> None:
    """CTRL-R4: versioned policy and production dispatch boundaries hold."""
    tests = REPO_ROOT / "test" / "harness" / "controller_routing_r4_tests.py"
    proc = subprocess.run([sys.executable, str(tests)], cwd=REPO_ROOT,
                          capture_output=True, text=True, timeout=120)
    detail = (proc.stdout + proc.stderr).strip()
    r.add("CTRL-R4", "rigour-auto-v1 policy and crash-safe Controller dispatch hold",
          proc.returncode == 0,
          detail.splitlines()[-1] if proc.returncode == 0 else detail[-2000:])


def check_controller_evaluation_r5(r: Report) -> None:
    """CTRL-R5A: offline corpus, score and launch manifests remain frozen."""
    tests = REPO_ROOT / "test" / "harness" / "controller_evaluation_r5_tests.py"
    proc = subprocess.run([sys.executable, str(tests)], cwd=REPO_ROOT,
                          capture_output=True, text=True, timeout=120)
    detail = (proc.stdout + proc.stderr).strip()
    r.add("CTRL-R5A", "R5 corpus blueprints, scoring and paid launch manifests hold offline",
          proc.returncode == 0,
          detail.splitlines()[-1] if proc.returncode == 0 else detail[-2000:])


ALLOWED_PRIOR_KINDS = {"measured", "bracketed", "policy-inherited", "policy-default"}


def check_route_priors(r: Report) -> None:
    """ROUTE-PRIORS: tools/generate_priors.py's output matches the committed
    src/routing_priors.json byte for byte (run with --check, which writes
    nothing), and every bucket's floor and every rung entry carries
    non-empty provenance and a kind in the allowed set (docs/PLAN-2.md
    Stage 2.5, D64)."""
    script = REPO_ROOT / "tools" / "generate_priors.py"
    priors_path = SRC / "routing_priors.json"
    if not script.exists() or not priors_path.exists():
        r.add("ROUTE-PRIORS", "priors match their generator and carry provenance", False,
              f"{script.relative_to(REPO_ROOT)} or {priors_path.relative_to(REPO_ROOT)} missing")
        return
    proc = subprocess.run([sys.executable, str(script), "--check"], capture_output=True, text=True, timeout=30)
    if proc.returncode != 0:
        r.add("ROUTE-PRIORS", "priors match their generator and carry provenance", False,
              (proc.stdout + proc.stderr).strip()[-400:])
        return
    try:
        priors = json.loads(priors_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        r.add("ROUTE-PRIORS", "priors match their generator and carry provenance", False, f"invalid JSON: {exc}")
        return
    problems: list[str] = []
    for bucket, data in priors.get("buckets", {}).items():
        entries = ([("floor", data.get("floor", {})), ("overflow", data.get("overflow", {}))]
                   + [(f"rung {c}", v) for c, v in data.get("rungs_given_failure_below", {}).items()])
        for label, entry in entries:
            if not entry.get("provenance"):
                problems.append(f"{bucket} {label}: missing provenance")
            if entry.get("kind") not in ALLOWED_PRIOR_KINDS:
                problems.append(f"{bucket} {label}: kind {entry.get('kind')!r} not in {sorted(ALLOWED_PRIOR_KINDS)}")
    # docs/COMPACTION-DESIGN.md section 4: the handoff threshold must
    # recommend a handoff before the platform's own auto-compact window is
    # reached on the 200K reference model, or the two settings contradict
    # each other (a handoff urged after the platform already compacted).
    steering = priors.get("steering", {})
    handoff_pct, autocompact_tokens = steering.get("handoff_context_percent"), steering.get("autocompact_window_tokens")
    if handoff_pct is None or autocompact_tokens is None:
        problems.append("steering: missing handoff_context_percent or autocompact_window_tokens")
    elif handoff_pct / 100 * 200_000 >= autocompact_tokens:
        problems.append(f"steering: handoff_context_percent ({handoff_pct}% of 200,000) does not fire "
                         f"before autocompact_window_tokens ({autocompact_tokens})")
    if steering.get("overflow_advisory_min_mean") is None or steering.get("overflow_advisory_min_n") is None:
        problems.append("steering: missing overflow_advisory_min_mean or overflow_advisory_min_n")
    r.add("ROUTE-PRIORS", "priors match their generator and carry provenance", not problems,
          f"{len(priors.get('buckets', {}))} buckets, generator matches" if not problems else "; ".join(problems[:8]))


def check_cost_table(r: Report) -> None:
    """COST-TABLE: every cell and the controller row in src/cost_table.json
    carry provenance, regime and n, with n: 0 wherever a cost is null
    (unmeasured); the verdict block carries provenance and a regime for
    each figure it states (docs/PLAN-2.md Stage 2.5)."""
    path = SRC / "cost_table.json"
    if not path.exists():
        r.add("COST-TABLE", "every cost row carries provenance", False, f"{path.relative_to(REPO_ROOT)} missing")
        return
    try:
        costs = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        r.add("COST-TABLE", "every cost row carries provenance", False, f"invalid JSON: {exc}")
        return
    problems: list[str] = []
    for cell, row in costs.get("cells", {}).items():
        for field_name in ("provenance", "regime", "n"):
            if field_name not in row:
                problems.append(f"cells.{cell}: missing {field_name}")
        if row.get("cost_per_run_usd") is None and row.get("n") != 0:
            problems.append(f"cells.{cell}: null cost but n={row.get('n')!r}, expected 0")
    controller = costs.get("controller", {})
    for field_name in ("provenance", "regime", "n"):
        if field_name not in controller:
            problems.append(f"controller: missing {field_name}")
    verdict = costs.get("verdict", {})
    if not verdict.get("provenance") or not verdict.get("regime"):
        problems.append("verdict: missing provenance or regime")
    # The context section (docs/PLAN-3.md Stage A.3) mixes documented
    # platform constants with figures aggregated from recorded runs; each
    # subsection names its source so the two are never confused.
    context = costs.get("context")
    if context is None:
        problems.append("context: section missing")
    else:
        for name in ("multipliers", "ttl", "auto_compact", "compaction_cost", "measured"):
            block = context.get(name)
            if not isinstance(block, dict):
                problems.append(f"context.{name}: missing")
            elif not block.get("provenance"):
                problems.append(f"context.{name}: missing provenance")
        measured = context.get("measured", {})
        if isinstance(measured, dict) and measured.get("n_rows", 0) <= 0:
            problems.append("context.measured: n_rows must be positive")
    r.add("COST-TABLE", "every cost row carries provenance", not problems,
          f"{len(costs.get('cells', {}))} cells, controller, verdict and context rows carry provenance"
          if not problems else "; ".join(problems[:8]))


def check_replay(r: Report) -> None:
    """REPLAY: test/harness/replay_routing.py exits 0 (docs/ROUTING-2-DESIGN.md
    section 4's pass condition: pooled agreement on the recorded two-stage
    opus batch at or above D40's 92.2 percent, excluding policy-fired rows,
    D65; zero first: controller on any contained fixture)."""
    script = REPO_ROOT / "test" / "harness" / "replay_routing.py"
    if not script.exists():
        r.add("REPLAY", "replay_routing.py passes its own gate", False, f"{script.relative_to(REPO_ROOT)} missing")
        return
    proc = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=60)
    detail = next((line for line in proc.stdout.splitlines() if line.startswith("Gate result:")), proc.stdout.strip()[-400:])
    r.add("REPLAY", "replay_routing.py passes its own gate", proc.returncode == 0,
          detail if proc.returncode == 0 else (detail + " | " + (proc.stdout + proc.stderr).strip()[-400:]))


def check_backtest(r: Report) -> None:
    """BACKTEST: test/harness/backtest_ledger.py exits 0 (docs/ROUTING-2-DESIGN.md
    section 5's pass condition: every bucket stays at the floor, worker-
    opus-high activates for open/medium/contained, no intermediate sonnet
    rung activates anywhere, the Controller decision is not proactive on
    any contained bucket; D66 excludes one run D16 already invalidated;
    docs/PLAN-3.md Stage C.4 adds that every bucket's overflow posterior
    sits exactly at its shipped prior, since no reconstructed entry
    carries a context field)."""
    script = REPO_ROOT / "test" / "harness" / "backtest_ledger.py"
    if not script.exists():
        r.add("BACKTEST", "backtest_ledger.py passes its own pass conditions", False, f"{script.relative_to(REPO_ROOT)} missing")
        return
    proc = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=60)
    fails = [line for line in proc.stdout.splitlines() if line.startswith("- FAIL")]
    detail = f"{proc.stdout.count('- PASS')} pass, {len(fails)} fail" if proc.returncode == 0 or fails else proc.stdout.strip()[-400:]
    r.add("BACKTEST", "backtest_ledger.py passes its own pass conditions", proc.returncode == 0,
          detail if proc.returncode == 0 else (detail + " | " + "; ".join(fails[:5])))


def check_route_selftest(r: Report) -> None:
    """ROUTE-SELFTEST: tools/route.py's --selftest passes: 19 scripted
    ledger-aware scenarios (7 from docs/PLAN.md Stage 2.5's own task text;
    the spawn/record/recover round trip and the --explain context line
    from docs/PLAN-3.md Stage B; the overflow advisory firing and not
    firing from Stage C; transcript-first fill_context and the
    session-pointer round trip from docs/PLAN-4.md Stage C, section 13.1
    and 13.4; an unescalated floor failure lowering the posterior, and a
    project's own ledger-measured cost overriding cost_table.json in the
    expected ladder cost, from docs/PLAN-6.md Stage B.5 and B.8,
    D81/A4/A5), no claude -p calls."""
    script = REPO_ROOT / "tools" / "route.py"
    if not script.exists():
        r.add("ROUTE-SELFTEST", "route.py --selftest passes", False, f"{script.relative_to(REPO_ROOT)} missing")
        return
    proc = subprocess.run([sys.executable, str(script), "--selftest"], capture_output=True, text=True, timeout=30)
    r.add("ROUTE-SELFTEST", "route.py --selftest passes", proc.returncode == 0,
          proc.stdout.strip().splitlines()[-1] if proc.returncode == 0 else (proc.stdout + proc.stderr).strip()[-800:])


def check_qualified_default(r: Report) -> None:
    """QUALIFIED-DEFAULT: every task follows the exact B0 sequence."""
    script = REPO_ROOT / "test" / "harness" / "qualified_default_tests.py"
    proc = subprocess.run(
        [sys.executable, str(script)], cwd=REPO_ROOT,
        capture_output=True, text=True, timeout=90,
    )
    r.add("QUALIFIED-DEFAULT", "reserved-qualified B0 is the fixed shipping policy",
          proc.returncode == 0, (proc.stdout + proc.stderr).strip()[-1600:])


def check_worker_selector_n3(r: Report) -> None:
    """WORKER-N3: all cells, public evidence, overrides and B0 isolation."""
    script = REPO_ROOT / "test" / "harness" / "worker_selector_n3_tests.py"
    proc = subprocess.run([sys.executable, str(script)], cwd=REPO_ROOT,
                          capture_output=True, text=True, timeout=90)
    r.add("WORKER-N3", "experimental worker selector and B0 isolation pass offline",
          proc.returncode == 0, (proc.stdout + proc.stderr).strip()[-1600:])


def check_worker_n4(r: Report) -> None:
    """N4: deterministic corpus, fake campaign and predeclared paired bounds."""
    scripts = (("worker_corpus_n4_tests.py", 150),
               ("worker_evaluation_n4_tests.py", 90),
               ("worker_statistics_n4_tests.py", 30))
    problems = []
    for name, timeout in scripts:
        proc = subprocess.run([sys.executable, str(REPO_ROOT / "test" / "harness" / name)],
                              cwd=REPO_ROOT, capture_output=True, text=True, timeout=timeout)
        if proc.returncode:
            problems.append(f"{name}: {(proc.stdout + proc.stderr).strip()[-800:]}")
    parity = subprocess.run([sys.executable, str(REPO_ROOT / "tools" / "worker_corpus.py"),
                             "--check"], cwd=REPO_ROOT, capture_output=True, text=True,
                            timeout=30)
    if parity.returncode:
        problems.append("corpus parity: " + (parity.stdout + parity.stderr).strip()[-800:])
    recorded = subprocess.run([sys.executable, str(REPO_ROOT / "tools" / "worker_graft_probe.py"),
                               "--check"], cwd=REPO_ROOT, capture_output=True, text=True,
                              timeout=15)
    if recorded.returncode:
        problems.append("recorded actor-root Graft probe: " +
                        (recorded.stdout + recorded.stderr).strip()[-800:])
    r.add("WORKER-N4", "protected synthetic corpus and fake campaign pass offline",
          not problems, "all five checks pass" if not problems else "; ".join(problems))


def check_claudep_selftest(r: Report) -> None:
    """CLAUDEP-SELFTEST: subprocess failures retain recoverable invocation
    cost and usage metadata without making a live ``claude -p`` call."""
    script = REPO_ROOT / "tools" / "claudep.py"
    if not script.exists():
        r.add("CLAUDEP-SELFTEST", "claudep.py --selftest passes", False,
              f"{script.relative_to(REPO_ROOT)} missing")
        return
    proc = subprocess.run([sys.executable, str(script), "--selftest"], capture_output=True, text=True, timeout=30)
    r.add("CLAUDEP-SELFTEST", "claudep.py --selftest passes", proc.returncode == 0,
          proc.stdout.strip().splitlines()[-1] if proc.returncode == 0 else (proc.stdout + proc.stderr).strip()[-800:])


def check_dispatch_budget(r: Report) -> None:
    """DISPATCH-BUDGET: atomic admission, failure accounting and safe recovery."""
    script = REPO_ROOT / "test" / "harness" / "dispatch_budget_tests.py"
    proc = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=60)
    r.add("DISPATCH-BUDGET", "Controller budget races and recovery pass", proc.returncode == 0,
          (proc.stdout + proc.stderr).strip()[-1200:])


def check_acceptance_evidence(r: Report) -> None:
    """ACCEPTANCE: contracts, exact artefacts, protected tests and recovery."""
    script = REPO_ROOT / "test" / "harness" / "acceptance_tests.py"
    proc = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=60)
    r.add("ACCEPTANCE", "acceptance evidence and incomplete recovery pass", proc.returncode == 0,
          (proc.stdout + proc.stderr).strip()[-1400:])


def check_context_contract(r: Report) -> None:
    """CONTEXT: static reduction and every mandatory instruction surface."""
    script = REPO_ROOT / "test" / "harness" / "context_contract_tests.py"
    proc = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=60)
    r.add("CONTEXT", "prompt reduction preserves the operating contract", proc.returncode == 0,
          (proc.stdout + proc.stderr).strip()[-1400:])


def check_installer(r: Report) -> None:
    """INSTALL: ownership, idempotence, conflicts and semantic rollback."""
    script = REPO_ROOT / "test" / "harness" / "install_tests.py"
    proc = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=120)
    r.add("INSTALL", "transactional install, upgrade, uninstall and rollback pass", proc.returncode == 0,
          (proc.stdout + proc.stderr).strip()[-1800:])


def check_diagnostics(r: Report) -> None:
    """DIAGNOSTICS: operational status is authoritative and read-only."""
    script = REPO_ROOT / "test" / "harness" / "diagnostic_tests.py"
    proc = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=60)
    r.add("DIAGNOSTICS", "operational status and detailed explanation pass", proc.returncode == 0,
          (proc.stdout + proc.stderr).strip()[-1400:])


def check_realworld_foundation(r: Report) -> None:
    """REALWORLD: isolated external graders reject adversarial repairs offline."""
    script = REPO_ROOT / "test" / "harness" / "realworld_tests.py"
    # The complete 24-task corpus runs 144 states plus protected-boundary
    # attacks twice (direct API and CLI regression paths). The direct run
    # exceeded five minutes on this Windows host; keep both full passes and
    # leave headroom without changing any per-task execution timeout.
    proc = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=900)
    r.add("REALWORLD", "24 real-world graders and candidate freeze pass offline", proc.returncode == 0,
          (proc.stdout + proc.stderr).strip()[-1800:])


def check_evaluation_runner(r: Report) -> None:
    """EPISODE: checkpoint, replay, accounting and failure-path regression."""
    tests = REPO_ROOT / "test" / "harness" / "evaluation_runner_tests.py"
    evidence = REPO_ROOT / "test" / "results" / "2026-09-17-realworld-runner.json"
    runner = REPO_ROOT / "tools" / "evaluation_runner.py"
    test_proc = subprocess.run([sys.executable, str(tests)], cwd=REPO_ROOT,
                               capture_output=True, text=True, timeout=90)
    evidence_proc = subprocess.run(
        [sys.executable, str(runner), "--check", "--output", str(evidence)],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
    )
    passed = test_proc.returncode == 0 and evidence_proc.returncode == 0
    detail = (test_proc.stdout + test_proc.stderr + "\n"
              + evidence_proc.stdout + evidence_proc.stderr).strip()[-1800:]
    r.add("EPISODE", "offline episode checkpoint and deterministic replay pass", passed, detail)


def check_live_calibration(r: Report) -> None:
    """CALIBRATION: offline parsers and integrity-bound live evidence pass."""
    tests = [
        REPO_ROOT / "test" / "harness" / "live_calibration_tests.py",
        REPO_ROOT / "test" / "harness" / "live_calibration_adjudication_tests.py",
    ]
    results = [subprocess.run(
        [sys.executable, str(path)], cwd=REPO_ROOT,
        capture_output=True, text=True, timeout=60,
    ) for path in tests]
    evidence = REPO_ROOT / "test" / "results" / "2026-09-17-live-calibration-adjudication.json"
    verifier = REPO_ROOT / "tools" / "live_calibration_adjudication.py"
    evidence_result = subprocess.run(
        [sys.executable, str(verifier), "--check", "--output", str(evidence)],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
    )
    passed = all(item.returncode == 0 for item in results) and evidence_result.returncode == 0
    detail = "\n".join(
        item.stdout + item.stderr for item in results + [evidence_result]
    ).strip()[-1800:]
    r.add("CALIBRATE", "live identity, billing and timeout evidence validates offline", passed, detail)


def check_live_worker_adapter(r: Report) -> None:
    """LIVE-WORKER: restricted command, attribution and failure paths pass."""
    tests = REPO_ROOT / "test" / "harness" / "evaluation_live_worker_tests.py"
    evidence = REPO_ROOT / "test" / "results" / "2026-09-17-live-worker-adapter.json"
    adapter = REPO_ROOT / "tools" / "evaluation_live_worker.py"
    test_result = subprocess.run(
        [sys.executable, str(tests)], cwd=REPO_ROOT,
        capture_output=True, text=True, timeout=90,
    )
    evidence_result = subprocess.run(
        [sys.executable, str(adapter), "--check", "--output", str(evidence)],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
    )
    passed = test_result.returncode == 0 and evidence_result.returncode == 0
    detail = (test_result.stdout + test_result.stderr + "\n"
              + evidence_result.stdout + evidence_result.stderr).strip()[-1800:]
    r.add("LIVE-WORKER", "live attempt adapter qualifies without model calls", passed, detail)


def check_live_controller_adapter(r: Report) -> None:
    """LIVE-CONTROLLER: nested accounting, identity and isolation pass."""
    tests = REPO_ROOT / "test" / "harness" / "evaluation_live_controller_tests.py"
    evidence = REPO_ROOT / "test" / "results" / "2026-09-18-live-controller-adapter.json"
    adapter = REPO_ROOT / "tools" / "evaluation_live_controller.py"
    test_result = subprocess.run(
        [sys.executable, str(tests)], cwd=REPO_ROOT,
        capture_output=True, text=True, timeout=90,
    )
    evidence_result = subprocess.run(
        [sys.executable, str(adapter), "--check", "--output", str(evidence)],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
    )
    passed = test_result.returncode == 0 and evidence_result.returncode == 0
    detail = (test_result.stdout + test_result.stderr + "\n"
              + evidence_result.stdout + evidence_result.stderr).strip()[-1800:]
    r.add("LIVE-CONTROLLER", "live Controller adapter qualifies without model calls",
          passed, detail)


def check_live_episode_integration(r: Report) -> None:
    """LIVE-EPISODE: policy ordering and at-most-once recovery pass."""
    tests = REPO_ROOT / "test" / "harness" / "evaluation_live_episode_tests.py"
    evidence = REPO_ROOT / "test" / "results" / "2026-09-17-live-episode-integration.json"
    runner = REPO_ROOT / "tools" / "evaluation_live_episode.py"
    test_result = subprocess.run(
        [sys.executable, str(tests)], cwd=REPO_ROOT,
        capture_output=True, text=True, timeout=90,
    )
    evidence_result = subprocess.run(
        [sys.executable, str(runner), "--check", "--output", str(evidence)],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
    )
    passed = test_result.returncode == 0 and evidence_result.returncode == 0
    detail = (test_result.stdout + test_result.stderr + "\n"
              + evidence_result.stdout + evidence_result.stderr).strip()[-1800:]
    r.add("LIVE-EPISODE", "live policy and restart safety qualify without model calls",
          passed, detail)


def check_pilot_preflight(r: Report) -> None:
    """PILOT-PREFLIGHT: fixed envelope and exact authorisation gate pass."""
    tests = REPO_ROOT / "test" / "harness" / "evaluation_pilot_tests.py"
    evidence = REPO_ROOT / "test" / "results" / "2026-09-18-pilot-preflight.json"
    runner = REPO_ROOT / "tools" / "evaluation_pilot.py"
    test_result = subprocess.run(
        [sys.executable, str(tests)], cwd=REPO_ROOT,
        capture_output=True, text=True, timeout=90,
    )
    evidence_result = subprocess.run(
        [sys.executable, str(runner), "--check", "--evidence", str(evidence)],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
    )
    passed = test_result.returncode == 0 and evidence_result.returncode == 0
    detail = (test_result.stdout + test_result.stderr + "\n"
              + evidence_result.stdout + evidence_result.stderr).strip()[-1800:]
    r.add("PILOT-PREFLIGHT", "paid pilot envelope qualifies without model calls",
          passed, detail)


def check_development_result(r: Report) -> None:
    """W07-RESULT: paid evidence is reconciled and integrity-bound offline."""
    tests = REPO_ROOT / "test" / "harness" / "evaluation_development_result_tests.py"
    evidence = REPO_ROOT / "test" / "results" / "2026-09-18-realworld-development.json"
    aggregator = REPO_ROOT / "tools" / "evaluation_development_result.py"
    test_result = subprocess.run(
        [sys.executable, str(tests)], cwd=REPO_ROOT,
        capture_output=True, text=True, timeout=90,
    )
    evidence_result = subprocess.run(
        [sys.executable, str(aggregator), "--check"], cwd=REPO_ROOT,
        capture_output=True, text=True, timeout=30,
    )
    passed = test_result.returncode == 0 and evidence_result.returncode == 0
    detail = (test_result.stdout + test_result.stderr + "\n"
              + evidence_result.stdout + evidence_result.stderr).strip()[-1800:]
    r.add("W07-RESULT", "W07 paid evidence reconciles and validates offline",
          passed, detail)


def check_reserved_result(r: Report) -> None:
    """W08-RESULT: reserved evidence and release-gate decision validate."""
    tests = REPO_ROOT / "test" / "harness" / "evaluation_reserved_result_tests.py"
    aggregator = REPO_ROOT / "tools" / "evaluation_reserved_result.py"
    test_result = subprocess.run(
        [sys.executable, str(tests)], cwd=REPO_ROOT,
        capture_output=True, text=True, timeout=90,
    )
    evidence_result = subprocess.run(
        [sys.executable, str(aggregator), "--check"], cwd=REPO_ROOT,
        capture_output=True, text=True, timeout=30,
    )
    passed = test_result.returncode == 0 and evidence_result.returncode == 0
    detail = (test_result.stdout + test_result.stderr + "\n"
              + evidence_result.stdout + evidence_result.stderr).strip()[-1800:]
    r.add("W08-RESULT", "W08 evidence and release-gate decision validate offline",
          passed, detail)


def check_release_candidate(r: Report) -> None:
    """RELEASE: source parity and redistribution exclusions are executable."""
    script = REPO_ROOT / "tools" / "release_check.py"
    proc = subprocess.run([sys.executable, str(script), "--json"], capture_output=True, text=True, timeout=60)
    try:
        value = json.loads(proc.stdout)
        detail = (f"mechanical failures={value['mechanical_failures']}; "
                  f"operator actions={value['operator_actions']}")
        ok = proc.returncode == 0 and not value["mechanical_failures"]
    except (json.JSONDecodeError, KeyError, TypeError):
        ok, detail = False, (proc.stdout + proc.stderr).strip()[-1200:]
    r.add("RELEASE", "release-candidate parity and redistribution checks run", ok, detail)


def check_improvement_regressions(r: Report) -> None:
    """AUDIT-REGRESSIONS: desired R1/R2/R3/R5 behaviour is executable;
    open findings are explicit expected failures rather than bug-affirming
    assertions."""
    script = REPO_ROOT / "test" / "harness" / "improvement_regressions.py"
    if not script.exists():
        r.add("AUDIT-REGRESSIONS", "audit desired-behaviour regressions run", False,
              f"{script.relative_to(REPO_ROOT)} missing")
        return
    proc = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=30)
    r.add("AUDIT-REGRESSIONS", "audit desired-behaviour regressions run", proc.returncode == 0,
          proc.stdout.strip().splitlines()[-1] if proc.returncode == 0 else (proc.stdout + proc.stderr).strip()[-800:])


def check_handoff_selftest(r: Report) -> None:
    """HANDOFF-SELFTEST: tools/handoff.py's --selftest passes: 5 scripted
    scenarios (a clean file, every corrupted section named, a missing
    front-matter comment, a spawn handoff's cell/controller cost, and
    --pending-workers from docs/PLAN-3.md Stage D), no claude -p calls
    (docs/PLAN-2.md Stage 3)."""
    script = REPO_ROOT / "tools" / "handoff.py"
    if not script.exists():
        r.add("HANDOFF-SELFTEST", "handoff.py --selftest passes", False, f"{script.relative_to(REPO_ROOT)} missing")
        return
    proc = subprocess.run([sys.executable, str(script), "--selftest"], capture_output=True, text=True, timeout=30)
    r.add("HANDOFF-SELFTEST", "handoff.py --selftest passes", proc.returncode == 0,
          proc.stdout.strip().splitlines()[-1] if proc.returncode == 0 else (proc.stdout + proc.stderr).strip()[-800:])


def check_probe_selftest(r: Report) -> None:
    """PROBE-SELFTEST: tools/context_probe.py's --selftest passes: both
    status line modes round-trip against the documentation-derived sample
    in test/fixtures/system/statusline-sample.json, plus the
    effective-window used_percentage recomputation against a configured
    autoCompactWindow, no claude -p calls (docs/PLAN-3.md Stage B,
    docs/COMPACTION-DESIGN.md section 11 and 13.2, docs/PLAN-4.md Stage C)."""
    script = REPO_ROOT / "tools" / "context_probe.py"
    if not script.exists():
        r.add("PROBE-SELFTEST", "context_probe.py --selftest passes", False, f"{script.relative_to(REPO_ROOT)} missing")
        return
    proc = subprocess.run([sys.executable, str(script), "--selftest"], capture_output=True, text=True, timeout=30)
    r.add("PROBE-SELFTEST", "context_probe.py --selftest passes", proc.returncode == 0,
          proc.stdout.strip().splitlines()[-1] if proc.returncode == 0 else (proc.stdout + proc.stderr).strip()[-800:])


def check_compact_bench_selftest(r: Report) -> None:
    """COMPACT-BENCH-SELFTEST: test/harness/compaction_bench.py's
    --selftest passes: extract_transcript and first_tool_use_lineno
    against the committed, redacted sample transcript, no claude -p calls
    (docs/PLAN-4.md Stage B.2, docs/COMPACTION-DESIGN.md section 13.6)."""
    script = REPO_ROOT / "test" / "harness" / "compaction_bench.py"
    if not script.exists():
        r.add("COMPACT-BENCH-SELFTEST", "compaction_bench.py --selftest passes", False,
              f"{script.relative_to(REPO_ROOT)} missing")
        return
    proc = subprocess.run([sys.executable, str(script), "--selftest"], capture_output=True, text=True, timeout=30)
    r.add("COMPACT-BENCH-SELFTEST", "compaction_bench.py --selftest passes", proc.returncode == 0,
          proc.stdout.strip().splitlines()[-1] if proc.returncode == 0 else (proc.stdout + proc.stderr).strip()[-800:])


def check_fixture_clean(r: Report) -> None:
    """FIXTURE-CLEAN: no file under a compaction-measurement fixture's
    `repo/` or its `task.md` names this repository (`docs/PLAN-4.md`
    Stage D found a worker read `make_chunks.py`'s own docstring, which
    cited this project's plans and decisions, and used that to refuse
    the whole task as synthetic; `docs/COMPACTION-DESIGN.md` section
    14.1 is the contract this check enforces). Scoped to T12 through T15
    (`T1[2-5]`), the shapes this repository has built for this purpose;
    an older benchmark fixture (T1 through T11) is not required to avoid
    these words, since none of them is read by a worker mid-compaction
    the way these are."""
    banned = re.compile(r"PLAN-|D7\d|E30|harness|benchmark|measurement|empirical|fixture", re.IGNORECASE)
    offenders = []
    for fixture_dir in sorted((REPO_ROOT / "test" / "fixtures" / "benchmark").glob("T1[2-5]")):
        candidates = [fixture_dir / "task.md"] + list((fixture_dir / "repo").glob("**/*")) \
            if (fixture_dir / "repo").is_dir() else [fixture_dir / "task.md"]
        for path in candidates:
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            m = banned.search(text)
            if m:
                offenders.append(f"{path.relative_to(REPO_ROOT)}: {m.group(0)!r}")
    r.add("FIXTURE-CLEAN", "no T12-T15 repo/ or task.md file self-references this repository",
          not offenders, f"{len(offenders)} offender(s): {offenders}" if offenders else "clean")


def check_interactive_checklist_selftest(r: Report) -> None:
    """INTERACTIVE-CHECKLIST-SELFTEST: test/harness/interactive_checklist.py's
    --selftest passes: --prepare and --check against a throwaway git
    repository, no claude -p calls (docs/PLAN-4.md Stage D.1)."""
    script = REPO_ROOT / "test" / "harness" / "interactive_checklist.py"
    if not script.exists():
        r.add("INTERACTIVE-CHECKLIST-SELFTEST", "interactive_checklist.py --selftest passes", False,
              f"{script.relative_to(REPO_ROOT)} missing")
        return
    proc = subprocess.run([sys.executable, str(script), "--selftest"], capture_output=True, text=True, timeout=30)
    r.add("INTERACTIVE-CHECKLIST-SELFTEST", "interactive_checklist.py --selftest passes", proc.returncode == 0,
          proc.stdout.strip().splitlines()[-1] if proc.returncode == 0 else (proc.stdout + proc.stderr).strip()[-800:])


def check_handoffs(r: Report) -> None:
    """HANDOFF: every file under handoffs/ passes `tools/handoff.py check`
    (docs/PLAN-2.md Stage 3.2): all ten headings present, in order, none
    empty or an unfilled placeholder, and the Cost/Time projection
    sections carry the exact line handoff.py would compute from the
    file's own recorded front-matter arguments."""
    script = REPO_ROOT / "tools" / "handoff.py"
    handoffs_dir = REPO_ROOT / "handoffs"
    if not script.exists():
        r.add("HANDOFF", "every handoffs/ file passes handoff.py check", False, f"{script.relative_to(REPO_ROOT)} missing")
        return
    files = sorted(handoffs_dir.glob("*.md")) if handoffs_dir.is_dir() else []
    if not files:
        r.add("HANDOFF", "every handoffs/ file passes handoff.py check", True, "no handoff files yet")
        return
    problems: list[str] = []
    for f in files:
        proc = subprocess.run([sys.executable, str(script), "check", str(f)], capture_output=True, text=True, timeout=30)
        if proc.returncode != 0:
            problems.append(f"{f.relative_to(REPO_ROOT)}: {(proc.stdout + proc.stderr).strip()[-400:]}")
    r.add("HANDOFF", "every handoffs/ file passes handoff.py check", not problems,
          f"{len(files)} file(s) checked" if not problems else "; ".join(problems[:5]))


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
    check_route_modes(report)
    check_route_total(report)
    check_row_backed(report)
    check_table_data(report)
    check_clarify(report)
    check_environment(report)
    check_available_models(report)
    check_invariant7(report)
    check_prose(report)
    check_persona_manifest(report, args.update_persona_manifest)
    check_dist(report)
    check_fixtures(report, defs)
    check_schemas(report)
    check_system_controller(report)
    check_controller_routing_r0(report)
    check_controller_integrity_r1(report)
    check_model_registry_r2(report)
    check_controller_control_r3(report)
    check_controller_routing_r4(report)
    check_controller_evaluation_r5(report)
    check_route_priors(report)
    check_cost_table(report)
    check_route_selftest(report)
    check_qualified_default(report)
    check_worker_selector_n3(report)
    check_worker_n4(report)
    check_claudep_selftest(report)
    check_dispatch_budget(report)
    check_acceptance_evidence(report)
    check_context_contract(report)
    check_installer(report)
    check_diagnostics(report)
    check_realworld_foundation(report)
    check_evaluation_runner(report)
    check_live_calibration(report)
    check_live_worker_adapter(report)
    check_live_controller_adapter(report)
    check_live_episode_integration(report)
    check_pilot_preflight(report)
    check_development_result(report)
    check_reserved_result(report)
    check_release_candidate(report)
    check_improvement_regressions(report)
    check_replay(report)
    check_backtest(report)
    check_handoff_selftest(report)
    check_probe_selftest(report)
    check_compact_bench_selftest(report)
    check_fixture_clean(report)
    check_interactive_checklist_selftest(report)
    check_handoffs(report)

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
        status = {"version": 1, "execution_status": "completed" if report.failed == 0 else "failed",
                  "result": "PASS" if report.failed == 0 else "FAIL", "git": git_rev,
                  "recorded_at": when.astimezone().isoformat(),
                  "result_path": out.relative_to(REPO_ROOT).as_posix(),
                  "result_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
                  "checks": [c.__dict__ for c in report.checks]}
        status_path = RESULTS_DIR / f"{when.strftime('%Y-%m-%d')}-harness-status.json"
        _atomic_write_bytes(status_path, (json.dumps(status, indent=2) + "\n").encode("utf-8"))
        print(f"recorded {out.relative_to(REPO_ROOT)}")
        # docs/PLAN-6.md D.3, audit C5: --record is the one point every
        # harness run that writes to test/results/ already passes through,
        # so it is where the index it needs to stay current gets rebuilt.
        index_script = REPO_ROOT / "test" / "harness" / "results_index.py"
        index_proc = subprocess.run([sys.executable, str(index_script)], capture_output=True, text=True, cwd=REPO_ROOT)
        print(index_proc.stdout.strip() if index_proc.returncode == 0
              else f"results_index.py failed:\n{(index_proc.stdout + index_proc.stderr).strip()[-500:]}")
    return 1 if report.failed else 0


if __name__ == "__main__":
    try:
        result = main(sys.argv[1:])
    except BaseException as exc:
        if "--record" in sys.argv[1:]:
            when = dt.datetime.now().astimezone()
            status = {"version": 1, "execution_status": "interrupted", "result": None,
                      "recorded_at": when.isoformat(),
                      "error": f"{type(exc).__name__}: {exc}"[:1000]}
            path = RESULTS_DIR / f"{when.strftime('%Y-%m-%d')}-harness-status.json"
            _atomic_write_bytes(path, (json.dumps(status, indent=2) + "\n").encode("utf-8"))
        raise
    sys.exit(result)
