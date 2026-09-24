# Worker orchestration setup

Licensed under the Apache License, Version 2.0. See `LICENSE` in the
distribution root.

This bundle installs a cost-routing layer for Claude Code subagents into a
consumer project: fifteen worker definitions spanning three model classes
(sonnet, opus, fable) at five effort levels each, and a routing document that
tells your top-level session (the "orchestrator") which one to spawn for a
given task. The reserved-qualified B0 policy always starts at the cheapest cell,
allows one same-cell repair, then one Opus-high fallback. It is
configuration, prose and Python tools. Graft MCP is a required local retrieval
dependency; register it in the consumer project before starting work.

Install from the `dist/` bundle, never from `src/`. The bundle is versioned in
`.claude/ORCHESTRATOR_VERSION`; quote that version in any report.

Citations to `docs/*.md` and `test/results/*.md` files anywhere in this
document, and a bare decision number (`D<n>`), point at this bundle's
source repository, not at files this bundle ships: they are provenance
for a human who wants to check the reasoning behind a claim, not
something you need on disk to install or use the bundle.

## Required Graft MCP setup

Register an installed Graft MCP server named `graft` against the consumer
project's own root. Do not copy a server path or indexed root from another
machine or repository. In Codex, configure it in `.codex/config.toml` with
`enabled = true` and `required = true`; the latter prevents startup/resume
without the server. In Claude Code, register it in project `.mcp.json` and
merge the six Graft read-tool permissions from `settings.fragment.json`.
Preserve other servers, permissions and hooks. Trust/approval requirements
of the host still apply; a copied project cannot grant itself trust.

Before using the bundle, verify that `graft_check_freshness` succeeds and a
scoped query returns source from this checkout. The orchestrator, every
generated worker and every Controller role carry the retrieval requirement.
They must report missing tools instead of silently skipping Graft. Other
machines need their own working Graft installation and configuration.

## Layout of the bundle

```
.claude/
  agents/
    WORKER_sonnet_low.md ... WORKER_fable_max.md   (the 15 worker definitions)
  commands/
    workers.md                                      (the /workers status command)
    controller.md                                   (inspect or set task, session, or project
                                                     Controller routing intent)
  ORCHESTRATOR_VERSION                              (date and source commit)
  B0_BRIEF.md                                       (a single-worker handover brief; not
                                                     currently invoked automatically, kept
                                                     for manual use as a cheap alternative)
tools/
  route.py                                          (records an assessment, prints
                                                     diagnostic evidence and returns the
                                                     fixed B0 first cell; ORCHESTRATOR.md
                                                     section 2 runs it on every task)
  handoff.py                                        (writes and checks the handoff files
                                                     ORCHESTRATOR.md's handoff section asks
                                                     for on a model or effort change)
  context_probe.py                                  (the statusLine and subagentStatusLine
                                                     commands settings.fragment.json wires
                                                     in; --main writes .claude/context-main.json,
                                                     --tasks writes .claude/context-tasks.json,
                                                     each command owning its own file so the
                                                     two cannot race; route.py --explain's
                                                     context line reads context-main.json)
  system_controller.py                              (the integrity-v1 Controller: retained
                                                     outside the qualified B0 default;
                                                     legacy-quick-v0 replays history)
  controller_integrity.py                           (frozen acceptance, candidate eligibility
                                                     and evidence-packet integrity)
  controller_control.py                             (atomic auto/on/off intent, scoped precedence,
                                                     stale-write protection; never dispatches work)
  controller_policy.py                              (pure RigourAssessment to RoutingDecision policy)
  controller_dispatch.py                            (crash-safe task budget, real Controller adapter,
                                                     validated evidence and worker handoff)
  model_registry.py                                (exact 15-cell identity, effort, role-profile
                                                     and cost-evidence resolver)
  worker_selector.py                               (public-evidence N3 shadow selection over all
                                                     cells; no automatic dispatch)
  task_executor.py                                 (durable B0 admission, recovery, independent
                                                     acceptance and read-only rollback audit)
  managed_delegation.py                            (opt-in, budgeted child DAG under one root)
  worker_adapter.py                                (one restricted Claude CLI call with explicit
                                                     actor-scoped Graft MCP configuration)
  dispatch_budget.py, acceptance.py                (root monetary balance and frozen acceptance)
  claudep.py, system_prompts.py,
  validate_records.py                               (the Controller's own dependencies)
src/
  routing_priors.json                               (the qualified B0 policy plus retained
                                                     per-bucket Bayesian diagnostics;
                                                     project history cannot alter default
                                                     dispatch)
  cost_table.json                                   (measured per-cell and Controller cost,
                                                     for route.py's arithmetic and
                                                     handoff.py's projections)
  routing_table.json                                (the floor plus the frontier
                                                     escalation rule; the two destinations
                                                     that exist above the ledger-driven
                                                     ladder)
  model_registry.json                              (Sonnet, Opus and Fable provider identities,
                                                     five efforts, availability, role eligibility,
                                                     qualification and nullable pricing)
  System/
    SYSTEM.md, STEPS.md                              (Controller design and phase reference)
    ROLES.md, TECHNIQUES.md, schemas/               (role, technique, record and Controller
                                                     evidence-packet contracts;
                                                     schemas/ also holds
                                                     RoutingLedgerEntry, the shape of one
                                                     line in .claude/routing-ledger.jsonl.
                                                     Do not remove these if you keep
                                                     tools/system_controller.py or
                                                     tools/route.py)
ORCHESTRATOR.md                                     (the stable operating core generated from
                                                     src/ORCHESTRATOR_CORE.md)
ORCHESTRATOR-REFERENCE.md                           (detailed routing/lifecycle reference,
                                                     loaded only for named triggers)
SELF-LEARNING.md                                    (what the per-project ledger learns,
                                                     what it does not, and how to tell
                                                     the two apart)
CONTROLLER.md                                       (maintained Controller function, phase,
                                                     budget, recovery and qualification
                                                     reference)
WORKER-SELECTOR.md                                  (N3 assessment schema, overrides, stops,
                                                     evidence limits and B0 isolation)
CLAUDE.template.md                                  (a starting CLAUDE.md for a new
                                                     project: the pointer line plus the
                                                     handoff rule that survives platform
                                                     compaction)
settings.fragment.json                              (merge into .claude/settings.json:
                                                     the status line commands, the
                                                     one-hour cache TTL, and the
                                                     SessionStart(compact) recovery hook)
README.md                                           (this file)
preflight.py                                        (checks the settings below)
install.py                                          (transactional plan/apply/status/
                                                     uninstall/rollback command)
bundle-manifest.json                                (owned file hashes, configuration
                                                     keys and backup locations)
```

This project's own `.claude/routing-ledger.jsonl` is not part of the bundle. `route.py`
creates it on first use (`--record`) and it grows as the project runs; do not copy one
from another project, since it is the project's local diagnostic learning record.
`SELF-LEARNING.md` states exactly what that self-learning does and does not do, including
its limits, not only the mechanics.

Before dispatch, copy `acceptance-contract.example.json` to a task-specific
contract and fill in its required outputs, constraints, protected paths and
verification command or review rubric. `route.py --spawn` freezes that contract.
Completion writes content-addressed evidence under `.claude/acceptance/`; only
evidence that still matches the contract and current artefacts can affect
capability learning. Cost records remain usable when acceptance is blocked or
unverified.

The N1 worker executor is an installable Python API for a single B0 root task.
It journals admissions and receipts, holds one root budget across repairs and
linked continuations, verifies a frozen acceptance contract, and retains each
attempt's output. The production adapter needs an explicit MCP configuration
containing only an actor-scoped Graft server. Its command requests restricted
Claude tools and the six Graft retrieval tools; it does not use `--safe-mode`,
which disables MCP. The offline fake tests cover execution and recovery. Live
host enforcement and interactive Agent-tool interception have not been
qualified, so the normal interactive routing flow does not call this executor
automatically yet. That integration belongs to later stages.

N2 adds explicit managed child plans through `tools/managed_delegation.py`.
The operator approves a bounded graph with dependencies, read/write scope,
one cell and allowance per child, nested envelopes and independent acceptance.
The executor admits each child under the same root budget and stops parent
completion if required child evidence is missing or stale. Ordinary B0 tasks
remain single-worker. See [`MANAGED-DELEGATION.md`](MANAGED-DELEGATION.md) for
the proposal schema, API and recovery rules. The current production adapter
reports that child isolation is unproven and rejects live managed delegation;
the full execution path has been exercised with fake hosts only.

Before rolling back an installation that has used the executor, run
`python3 tools/task_executor.py --audit --project .`. A nonzero result means
an open task or unresolved hold requires reconciliation before another launch.
Keep `.claude/task-executor-v2/` and its budget and journal files during a
rollback; an older bundle cannot safely infer that an uncertain call was free.

The shared worker persona is inlined into every definition, so the consumer
project needs no separate persona file. Nothing in this bundle depends on
anything else in this repository being present at install time. The retained
Controller is executable only when explicitly selected for deliberate use,
historical replay, diagnostics or rollback. Its direct-run default is
`integrity-v1`; `legacy-quick-v0` exists for historical comparison. If kept,
`tools/` and `src/System/` must land at the
project's root in the same relative layout so
`python3 tools/system_controller.py` can find its dependencies. Qualified B0
dispatch never invokes it.

The installed `/controller` command and `tools/controller_control.py` provide
durable operator intent before automatic dispatch is introduced. Values may be
`auto`, `on` or `off`, with precedence explicit request/CLI, task, session,
project, then shipped default (`auto`). A narrower `auto` deliberately defeats
a wider `on` or `off`. Session and task values survive compaction when their
identifiers are retained; a fresh session inherits only the project value.
Updates are atomic, reject stale revisions when requested and apply at the next
safe dispatch boundary. They never start a worker or paid model call. R4's
structured policy and dispatcher can consume the resolved snapshot explicitly;
the qualified B0 sequence below remains the automatic runtime default until the
candidate passes R5-R7 evaluation.

```bash
python3 tools/controller_control.py --project . status
python3 tools/controller_control.py --project . set --scope project --mode auto
python3 tools/controller_control.py --project . set --scope session --session-id "$CLAUDE_SESSION_ID" --mode on
python3 tools/controller_control.py --project . set --scope task --task-revision "<revision>" --mode off
python3 tools/controller_control.py --project . resolve --session-id "$CLAUDE_SESSION_ID" --task-revision "<revision>"
```

## Qualified default and local learning

The shipping policy is B0, selected by the completed reserved evaluation. It
always runs this bounded sequence:

1. one `worker-sonnet-low` attempt;
2. one `worker-sonnet-low` repair after observable failure;
3. one `worker-opus-high` fallback after another observable failure;
4. stop.

No assessment, project history, posterior, frontier signal or Controller rule
can skip the floor, add an attempt or alter that order. The 48-episode reserved
comparison accepted 12 of 24 B0 episodes and 10 of 24 adaptive B1 episodes.
B0 recorded two paired wins and no paired loss; B1 increased false successes
and cost 20.97 percent more per accepted result. B1 failed the predeclared
promotion gates, so its implementation remains only for reproducible history
and explicit rollback (D107, D108).

"Self-learning" does not mean model training. `route.py` recomputes local
Bayesian capability estimates, measured cost and duration, evidence
compatibility and the compaction advisory from
`.claude/routing-ledger.jsonl`. These values explain the project's history and
support future experiments, but do not control B0 dispatch. Inspect them with:

```bash
python3 tools/route.py --from-line "<assessment>" --project . --explain
python3 preflight.py --status --explain
```

`route.py --record` verifies the frozen acceptance contract against current
artefacts and protected paths before completing a version-2 row. A worker
claim, stale evidence, failed command or unreviewed rubric cannot train
capability. Measured cost remains useful even when acceptance is failed,
blocked or unknown. `SELF-LEARNING.md` gives the full data model, thresholds,
migration path and limitations.

## Transactional install, update and removal

Use the bundled installer for new installations and upgrades. It verifies
every payload hash, shows its exact target, changes, conflicts and prospective
backup directory before changing anything, and owns only the files and values
listed in `bundle-manifest.json`.

```bash
python3 dist/install.py plan --target /path/to/project
python3 dist/install.py apply --target /path/to/project
python3 dist/install.py status --target /path/to/project
```

Use the same commands from an unpacked redistribution by replacing
`dist/install.py` with `install.py`. Paths containing spaces are accepted.
`apply` is idempotent: applying the same bundle to unchanged owned values is a
no-op. An upgrade uses the same command and can replace an older file only
when its current hash matches the previous installer state.

The installer preserves unrelated settings, permissions, hooks, MCP servers
and `CLAUDE.md` text. Existing scalar values such as `statusLine`, or existing
files at bundle-owned paths, are reported as conflicts instead of being
overwritten. Resolve the named conflict manually and rerun `plan`; malformed
JSON is never replaced.

Graft's executable is machine-specific, so it is not guessed. To let the
installer own `mcpServers.graft`, supply the command and each argument:

```bash
python3 dist/install.py apply --target /path/to/project \
  --graft-command /path/to/node --graft-arg /path/to/graft/cli.js \
  --graft-arg mcp --graft-arg .
```

Omitting these flags leaves `.mcp.json` untouched. Configure Graft manually
when another host owns that entry.

Every mutation stores preimages and semantic configuration operations under
`.claude/orchestrator-install/backups/<operation-id>/`. To remove the current
bundle or reverse the last install or upgrade:

```bash
python3 dist/install.py uninstall --target /path/to/project
python3 dist/install.py rollback --target /path/to/project
python3 dist/install.py rollback --target /path/to/project --backup <operation-id>
```

Rollback restores bundle files and owned values while retaining unrelated
configuration edits made later. It refuses the whole rollback when an owned
file or value changed after the recorded operation. The conflict report names
the path; the backup contains the exact preimage for manual recovery. The
backup root installs a deny-by-default `.gitignore` because preimages can
contain local settings or credentials. An
uninstall keeps backups, project ledgers, acceptance evidence, run records and
handoffs because those are project data rather than bundle payload.

After application, run `python3 preflight.py --status`. Add `--explain` for
per-attempt actual-versus-requested model evidence and outstanding acceptance
records, or `--json` for the stable schema used by automation.

## Manual install into a new project

The steps below remain available for inspection or a host that cannot run the
installer. They do not create ownership metadata or automatic rollback.

A project with no `CLAUDE.md` and no `.claude/agents/` yet.

1. Copy the bundle in, from this repository's root:

   Bash:
   ```bash
   CONSUMER=/path/to/your/project
   mkdir -p "$CONSUMER/.claude" "$CONSUMER/tools" "$CONSUMER/src/System" "$CONSUMER/handoffs"
   cp -r dist/.claude/. "$CONSUMER/.claude/"
   cp dist/ORCHESTRATOR.md dist/ORCHESTRATOR-REFERENCE.md dist/README.md dist/preflight.py \
      dist/acceptance-contract.example.json "$CONSUMER/"
   cp dist/tools/*.py "$CONSUMER/tools/"
   cp dist/src/*.json "$CONSUMER/src/"
   cp -r dist/src/System/. "$CONSUMER/src/System/"
   ```

   PowerShell:
   ```powershell
   $Consumer = "C:\path\to\your\project"
   New-Item -ItemType Directory -Force "$Consumer\.claude","$Consumer\tools","$Consumer\src\System","$Consumer\handoffs" | Out-Null
   Copy-Item -Recurse -Force "dist\.claude\*" "$Consumer\.claude\"
   Copy-Item -Force "dist\ORCHESTRATOR.md","dist\ORCHESTRATOR-REFERENCE.md","dist\README.md","dist\preflight.py","dist\acceptance-contract.example.json" "$Consumer\"
   Copy-Item -Force "dist\tools\*.py" "$Consumer\tools\"
   Copy-Item -Force "dist\src\*.json" "$Consumer\src\"
   Copy-Item -Recurse -Force "dist\src\System\*" "$Consumer\src\System\"
   ```

   The `tools/` and `src/System/` copies are what let `ORCHESTRATOR.md`
   section 4 actually run the Controller when its trigger fires; skip them
   only if you have deliberately decided not to use that trigger (see "Known
   limits" below). `acceptance-contract.example.json` is operational
   documentation: make one
   task-specific copy and edit the copy before dispatch. The `src/*.json` copy
   and the `handoffs/`
   directory are not optional the same way: `ORCHESTRATOR.md` section 2
   resolves every task through `tools/route.py`, which fails outright
   without `routing_priors.json`, `cost_table.json`, and
   `routing_table.json` in place (`preflight.py` checks for them).

2. Merge `dist/settings.fragment.json` into `$CONSUMER/.claude/settings.json`
   (create the file if it does not exist). It sets `promptCacheTtl: "1h"`, the
   `statusLine` and `subagentStatusLine` commands that give `route.py --explain`
   its context reading, a `permissions.allow` entry for `Bash(python3 *)` so
   `route.py` runs on every task without a per-call approval prompt (the
   settings table below), and a `SessionStart` hook (matcher `compact`) that
   runs `route.py --recover` after a platform compaction. If your project
   already has any of these keys, merge them by hand rather than overwriting:
   chain an existing `statusLine`/`subagentStatusLine` command to
   `context_probe.py` (run one, then the other), append the
   `Bash(python3 *)` entry to an existing `permissions.allow` array rather
   than replacing it, and add the `SessionStart` entry alongside any
   existing hooks for that event rather than replacing the array.

   The fragment carries `autoCompactWindow: 200000` as a real key, merged
   into this project's own `.claude/settings.json` at project scope, which
   is confirmed to take effect, not only user scope (`docs/FINDINGS.md`
   "Plan 4 Stage D"). If you would rather set it in
   `~/.claude/settings.json` for a user-wide default, or export
   `CLAUDE_CODE_AUTO_COMPACT_WINDOW=200000` instead, drop the fragment's
   `autoCompactWindow` key when merging; either overrides it, so leaving
   it in does no harm but is redundant. `preflight.py` (step 4 below)
   checks whichever you chose. Skip this step only if you have
   deliberately decided not to use the compaction mechanism at all (see
   "Known limits" below); `route.py --explain`'s context line then always
   reads "unknown" and never recommends a handoff, which is a silent
   degradation, not a failure.

3. Give the project a `CLAUDE.md` that reads `ORCHESTRATOR.md`. If the
   project has none yet, copy `dist/CLAUDE.template.md` to `CLAUDE.md`: it
   has the pointer line and the standing handoff rule (write a file under
   `handoffs/` with `tools/handoff.py` whenever this session's own model or
   effort must change). Otherwise add just the pointer line to the
   existing file:

   ```
   Read ORCHESTRATOR.md before delegating any task.
   ```

   A session only reads `ORCHESTRATOR.md` if something points it there; the
   pointer line is what makes that automatic. If the project already has a
   `CLAUDE.md` for other purposes, add the line to it rather than replacing
   the file (see "Install into an existing project" below).

   **Add the "Handoffs" section too, not only the pointer line, and do it
   by copying its actual text rather than pointing at where it lives.**
   The platform's own compaction mechanism reads instructions from
   `CLAUDE.md` itself, which is loaded once at session start and held
   outside the conversation; `ORCHESTRATOR.md` is not loaded that way; a
   session sees it only if it uses the Read tool on the pointer line,
   which puts its content inside the conversation, the exact thing a
   compaction replaces. A project that adds only the bare pointer line
   gets automatic routing but the handoff rule never survives a
   compaction the platform performs on its own, since it never entered
   `CLAUDE.md` in the first place. Copying the section's text directly
   into `CLAUDE.md` (`dist/CLAUDE.template.md` has it, ready to copy) is
   what makes it visible to the platform; pointing at `ORCHESTRATOR.md`
   for it is not equivalent to appending it. (An earlier version of this
   bundle also shipped a `# Compact instructions` section, asking the
   platform to keep a handoff's shape when it compacts on its own;
   removed, `docs/PLAN-4.md` Stage E.1: a pre-registered measurement
   across three task shapes found no shape where it lowered the
   constraint-violation rate against the unmodified default, so it no
   longer ships and there is nothing left to add here for it.)

4. Run the preflight check from the project root:

   ```bash
   python3 preflight.py
   ```

   It checks every row of the settings table further down except organisation
   effort limits, which needs an administrator to confirm. Fix anything it
   reports `FAIL` before proceeding; a `WARN` is informational.

5. **Restart Claude Code.** A worker definition added to `.claude/agents/`
   before your session started is not picked up by that session no matter how
   long you wait (confirmed empirically, `docs/FINDINGS.md`). Since this is a
   brand-new `.claude/agents/` directory, every session open at install time
   needs a restart to see it. Start a fresh session in the project after
   restarting.

6. Verify the install (see "Verifying it works" below) before delegating real
   work through it.

## Manual install into an existing project

A project that already has a `CLAUDE.md`, and possibly its own
`.claude/agents/` definitions.

1. Check for name collisions first. This bundle's worker definitions are
   named `worker-sonnet-low` through `worker-fable-max` (fifteen names, one
   per model/effort pair):

   ```bash
   ls "$CONSUMER/.claude/agents/" 2>/dev/null | grep -i "^WORKER_"
   ```

   If none of your existing agent files start with `WORKER_`, there is no
   collision; copy `dist/.claude/agents/*` and `dist/.claude/commands/workers.md`
   in alongside whatever is already there. `.claude/agents/` is a directory of
   independent files, so this is additive, not a merge that can silently drop
   an existing definition.

2. Copy `ORCHESTRATOR_VERSION` and `B0_BRIEF.md` into `.claude/`, and
   `ORCHESTRATOR.md` and `preflight.py` into the project root, the same way as
   a new install (step 1 above). If a previous version of this bundle is
   already installed, these overwrite it; the version file's old value is
   what you are upgrading from, worth noting before you overwrite it.

   **Check `tools/` and `src/System/` before copying into them.** Unlike
   `.claude/agents/`, an existing project very plausibly already has its
   own `tools/` and `src/` directories full of its own application code,
   and this bundle's file names (`claudep.py`, `system_prompts.py`, a
   `System/` subdirectory) are generic enough to collide:

   ```bash
   ls "$CONSUMER/tools/"*.py "$CONSUMER/src/System" 2>/dev/null
   ```

   If that lists anything you did not just put there, do not overwrite it
   sight unseen. Either place this bundle's Controller files under a
   dedicated subdirectory instead (for example `tools/orchestrator/` and
   `src/System/`, adjusting the paths `ORCHESTRATOR.md` section 4 uses to
   match, since the scripts resolve every other path relative to their own
   location), or skip shipping the Controller into this project at all and
   remove or edit section 4's trigger to stop at `worker-opus-high`
   directly, the same fallback it already uses if the Controller errors.
   `B0_BRIEF.md` still works as a cheaper manual alternative either way.

3. Copy `dist/tools/*.py` into `$CONSUMER/tools/`, `dist/src/*.json` into
   `$CONSUMER/src/`, and `dist/src/System/` into `$CONSUMER/src/System/`
   (or your chosen alternative location from the check above), the same
   commands as step 1 of a new install. Create `$CONSUMER/handoffs/` if it
   does not already exist.

4. Merge `dist/settings.fragment.json` into `$CONSUMER/.claude/settings.json`,
   same as step 2 of a new install: an existing project is exactly where a
   `statusLine`, `subagentStatusLine`, `permissions.allow`, `autoCompactWindow`,
   or `SessionStart` hook is likely to already be configured, so merge key
   by key rather than overwriting. If `autoCompactWindow` is already set,
   leave the existing value; the fragment's own `200000` is a default, not
   a requirement.

5. Add the line `Read ORCHESTRATOR.md before delegating any task.` to the
   existing `CLAUDE.md` rather than replacing the file. Where you add it
   matters less than that it is present; a natural place is near the top,
   beside any other file the project's `CLAUDE.md` already tells a session to
   read first. Copy `dist/CLAUDE.template.md`'s "Handoffs" section's actual
   text into `CLAUDE.md` too, if the project has none already: the
   platform's compaction reads instructions from `CLAUDE.md` itself, loaded
   once and held outside the conversation, not from `ORCHESTRATOR.md`,
   which a session only sees by reading it into the conversation the
   pointer line points at, the exact content a compaction replaces.
   Pointing at where the section lives is not the same as putting it where
   the platform looks.

   If `CLAUDE.md` already contains routing or delegation instructions from
   something else, decide whether they conflict before adding this bundle's:
   this bundle's routing table is meant to be the single source of truth for
   which worker to spawn (`src/ROUTING.md`'s own "Critical: this file does
   not route" section explains why a second, competing set of rules is worse
   than none).

6. Run `python3 preflight.py` from the project root, same as a new install.

7. Restart Claude Code **only if `.claude/agents/` did not already exist**
   before this session started. If the directory already existed (which it
   will, for most existing projects that already delegate to any subagent),
   the fifteen new definitions are picked up without a restart, typically
   within a turn or two. If you are not sure whether the directory predates
   your current session, restart anyway; it costs a few seconds and removes
   the question.

8. Verify the install before delegating real work through it.

## Verifying it works

Three checks, cheapest first:

1. **`python3 preflight.py`**'s "bundle installed" row: counts the
   worker definitions actually on disk under `.claude/agents/` against
   the fifteen expected and reports the installed bundle version. If it
   reports fewer than fifteen, files are missing or a restart is still
   needed. `/workers` (this bundle's own status command) reports on
   workers running or finished in the current session, not on which
   definitions are installed; it is a check on the next step, not this
   one.
2. **Spawn one worker and watch `/tasks` while it runs.** The row shows the
   model and, because every definition sets `effort` explicitly, the effort
   level. Ask for something small and unambiguous first (a mechanical task,
   which should route to `worker-sonnet-low`) so you have a known-correct
   answer to check the row against. If the row shows a different model or no
   effort level, a substitution happened somewhere upstream of this bundle
   (`availableModels`, an organisation cap, or one of the environment
   variables in the table below) rather than in the routing logic itself.
   Requires Claude Code v2.1.243 or later for the effort level to appear on
   the row at all.
3. **Read the orchestrator's one-line routing statement.** `ROUTING.md`
   section 3 asks the orchestrator to state, after spawning, which worker it
   chose and the assessment that justified it. If that line never appears,
   the orchestrator is not reading `ORCHESTRATOR.md` at all, which means
   step 2 above (`CLAUDE.md`'s pointer line) did not take effect; check it is
   present and that you restarted after adding it.

Do not treat a plausible-looking result as evidence of correct routing on its
own. A worker at the wrong cell can still produce a decent answer; the only
way to know it was the wrong cell is to read the `/tasks` row.

## Settings that will break this

`python3 preflight.py` checks these mechanically; the table explains why each
one matters and is what the script's messages point back to.

| Setting | Required state | Why |
| :--- | :--- | :--- |
| `CLAUDE_CODE_EFFORT_LEVEL` | unset | Overrides frontmatter `effort` on every worker. Frontmatter overrides the session level but not this variable. |
| `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` | unset or `0` | When on, Claude Code ignores the `model` field of every worker definition and flattens the whole scheme onto one model. |
| `CLAUDE_CODE_SUBAGENT_MODEL` | unset | A default for workers without a model. Harmless here since every worker sets one, but leave it clear to avoid confusion. |
| `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` | unset | With agent teams on, a named subagent launches as a teammate instead, and teammates follow the lead's effort level rather than their own definition. Naming is required for addressability, so this variable silently defeats the effort routing. |
| `availableModels` | must permit sonnet, opus, and fable | A blocked model is substituted, not failed. Interactive sessions warn; check the warning rather than assuming. |
| `Bash(python3 *)` in `.claude/settings.json` | permitted | `ORCHESTRATOR.md` section 2 shells out to `tools/route.py` on every task. Without this permission, Claude Code prompts for approval on every single routing call, which defeats the point of automatic routing. |
| Organisation effort limits | check with your admin | Enterprise roles can cap effort per model. A capped level runs at the cap, silently under `json` output or in background agents. |

## Upgrading to a newer bundle version

Run the new bundle's `install.py plan`, review the version, changes, conflicts
and backup path, then run `apply`. Files from an installer-managed older
version update only when their current hashes match its state. Configuration
values update only when the values still match what that older version owned.
This prevents an upgrade from erasing intervening operator edits.

A project installed manually before ownership manifests were introduced has
no safe provenance for same-name files. The installer reports those paths as
conflicts rather than adopting and later deleting them. Back up the project,
compare each named file with the old bundle, remove confirmed old payload
files, and run `plan` again. Keep project data such as routing ledgers,
acceptance evidence, run directories and handoffs.

After `apply`, run `python3 preflight.py --status --explain`. Restart only if
`.claude/agents/` did not exist before the current session. The source
repository's `docs/DECISIONS.md` explains changes keyed by the commit in
`ORCHESTRATOR_VERSION`.

## Known limits

- No true pause. Stop and resume only, and a user-stopped worker cannot be
  resumed at all. The user-stopped case is observed behaviour, unverified
  against the documentation as of 2026-09-05.
- 20 concurrent workers per session. Resuming a finished worker takes a fresh
  slot without checking the limit, so resumes can push you past it.
- Workers nest three layers deep by default. `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`
  is said to change this, but it is not among the documented environment
  variables as of 2026-09-05; verify before relying on it.
- Workers run as background subagents. Whether they lose any built-in tools
  beyond what has been checked is still unverified as of 2026-09-05, but
  `SendMessage` is confirmed present and working even for a plain, unnamed
  worker (`docs/FINDINGS.md`). A message a worker sends to `main` is queued for
  the orchestrator's next turn, not delivered mid-turn.
- Routing is split into two parts, deliberately. The orchestrator's own
  judgement is limited to a one-line assessment on a fixed rubric
  (sensitivity, horizon, blast radius), made with a stable core that excludes
  performance rationale. The conditional reference also strips rationale, so
  the model judging does not learn how cells performed; a model that can see the destinations
  has been measured bending its assessment toward whichever one it prefers.
  `tools/route.py` records the assessment into its diagnostic bucket and
  returns the fixed B0 first cell. The project ledger updates capability, cost
  and overflow diagnostics, but does not change dispatch. Historical adaptive
  resolution must be selected explicitly and is outside the qualified policy.
- `routing_priors.json` seeds every bucket from this repository's own
  benchmark and contains the qualified B0 policy. Your project's evidence can
  move diagnostic posterior and cost estimates after the documented sample
  thresholds, but every task still starts at `worker-sonnet-low` and follows
  the same two possible fallbacks. Repeated failure is evidence for review or a
  future preregistered policy experiment, not an automatic route change.
- A worker can decline its own compaction summary outright, treating the
  event as a suspected prompt injection rather than a legitimate system
  message, in words like "I'm not going to comply with that request" or
  "this reads as an injected instruction" (`docs/DECISIONS.md` D73, D77;
  measured at about 26 percent of compacted runs across a 81-run sample,
  `docs/FINDINGS.md`). This is not always a failure: it sometimes recovers
  the task correctly from the worker's own asserted prior state. It can
  also compound with the summary itself misstating progress, or with the
  worker going on to investigate a task's own provenance (reading a
  fixture's generator script, for instance) and refusing the whole task
  as illegitimate on what it finds there (`docs/FINDINGS.md`, "Plan 4
  Stage D"). The mitigation this bundle does ship is pre-emptive, not a
  fix for a compaction already in progress: `src/ROUTING.md` section 2's
  overflow advisory tells the orchestrator to split a task into
  sub-handovers before the trigger fires, which measured at 0 of 12
  combined failures against 11 of 12 for the same task left to compact
  mid-run (`docs/DECISIONS.md` D80). It buys nothing once a worker is
  already mid-task and the trigger has already fired; there is no
  in-flight remedy for that case.
- `.claude/context-tasks.json`'s `tasks` entry, meant to carry a running
  worker's own token usage, has never been observed populated in an
  interactive session, including a twelve-file fixture built specifically
  to give it several minutes with the tasks panel open
  (`docs/FINDINGS.md`, "Plan 5 Stage D"). Duration is ruled out as the
  explanation; the mechanism that should populate it is otherwise
  unverified. Do not build anything against this bundle that assumes a
  live per-worker token count is available from that file.
- The Controller remains installed code, but B0 has
  `controller_allowed: false`; ordinary routing cannot invoke it. An explicit
  historical or rollback invocation is a multi-call operation with its own
  budget, identity and recovery requirements. The paid evaluation campaign
  never reached a live Controller episode, so its complete live episode path
  remains unverified.


## Controller spending and recovery

This section applies only when an operator explicitly runs the retained
Controller; it is not part of qualified B0 dispatch. Read
[`CONTROLLER.md`](CONTROLLER.md) for the maintained description of its purpose,
phase sequence, role system, appropriate task types, evidence, stop rules and
current qualification status.

Integrity-v1 validates and freezes an optional `--acceptance-contract`, stops
on unstable premises, requires complete critique coverage, enforces Selector
exclusions and writes `controller-evidence.json`. The packet binds the input
revision, criteria, findings, uncertainty, artefact hashes, readiness and
accounting. Without an external contract, the first Frame criteria are
provisional and the packet cannot claim `verified-ready`.

The Controller's default USD 4 dispatch budget applies to one run. Roles,
classifiers, retries and parallel generators reserve from that balance before
launch. Later worker instantiation and other runs need separate allowances.
Read `budget-status.json` beside `REPORT.md`: unknown charges retain reservations
and a reported overrun blocks further work. This is local dispatch enforcement,
not a verified provider invoice ceiling.

To recover an interrupted run without repeating provider calls, run
`python3 tools/system_controller.py --recover-run runs/<id>` and read the created
`RECOVERY.md`. To stop new work in an active run, use `--cancel-run runs/<id>`.
Already running calls may still incur charges. The lifecycle section in
`ORCHESTRATOR.md` describes evidence-based reconciliation, per-request output
settings and optional elapsed-time limits. Recovery restores accounting and
reports; automatic pipeline continuation is not provided.
