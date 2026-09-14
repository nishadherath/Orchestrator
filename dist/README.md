# Worker orchestration setup

This bundle installs a cost-routing layer for Claude Code subagents into a
consumer project: fifteen worker definitions spanning three model classes
(sonnet, opus, fable) at five effort levels each, and a routing document that
tells your top-level session (the "orchestrator") which one to spawn for a
given task, defaulting to the cheapest and escalating only on evidence. It is
configuration and prose; there is no build step and no server to run.

Install from the `dist/` bundle, never from `src/`. The bundle is versioned in
`.claude/ORCHESTRATOR_VERSION`; quote that version in any report.

## Layout of the bundle

```
.claude/
  agents/
    WORKER_sonnet_low.md ... WORKER_fable_max.md   (the 15 worker definitions)
  commands/
    workers.md                                      (the /workers status command)
  ORCHESTRATOR_VERSION                              (date and source commit)
  B0_BRIEF.md                                       (a single-worker handover brief; not
                                                     currently invoked automatically, kept
                                                     for manual use as a cheap alternative)
tools/
  system_controller.py                              (the Controller: a quick-mode multi-
                                                     role state machine ORCHESTRATOR.md
                                                     section 4 invokes with the Bash tool
                                                     on one scoped escalation trigger)
  claudep.py, system_prompts.py,
  validate_records.py                               (the Controller's own dependencies)
src/System/
  ROLES.md, TECHNIQUES.md, schemas/                 (what the Controller reads at
                                                     runtime; do not remove these if you
                                                     keep tools/system_controller.py)
ORCHESTRATOR.md                                     (ROUTING.md + LIFECYCLE.md)
README.md                                           (this file)
preflight.py                                        (checks the settings below)
```

The shared worker persona is inlined into every definition, so the consumer
project needs no separate persona file. Nothing in this bundle depends on
anything else in this repository being present at install time. The
Controller is the one exception to "nothing to run": `tools/` and
`src/System/` must land at the project's root, in that same relative
layout, or `python3 tools/system_controller.py` will not find its own
dependencies when `ORCHESTRATOR.md` section 4 tries to invoke it.

## Install into a new project

A project with no `CLAUDE.md` and no `.claude/agents/` yet.

1. Copy the bundle in, from this repository's root:

   Bash:
   ```bash
   CONSUMER=/path/to/your/project
   mkdir -p "$CONSUMER/.claude" "$CONSUMER/tools" "$CONSUMER/src/System"
   cp -r dist/.claude/. "$CONSUMER/.claude/"
   cp dist/ORCHESTRATOR.md dist/README.md dist/preflight.py "$CONSUMER/"
   cp dist/tools/*.py "$CONSUMER/tools/"
   cp -r dist/src/System/. "$CONSUMER/src/System/"
   ```

   PowerShell:
   ```powershell
   $Consumer = "C:\path\to\your\project"
   New-Item -ItemType Directory -Force "$Consumer\.claude","$Consumer\tools","$Consumer\src\System" | Out-Null
   Copy-Item -Recurse -Force "dist\.claude\*" "$Consumer\.claude\"
   Copy-Item -Force "dist\ORCHESTRATOR.md","dist\README.md","dist\preflight.py" "$Consumer\"
   Copy-Item -Force "dist\tools\*.py" "$Consumer\tools\"
   Copy-Item -Recurse -Force "dist\src\System\*" "$Consumer\src\System\"
   ```

   The `tools/` and `src/System/` copies are what let `ORCHESTRATOR.md`
   section 4 actually run the Controller when its trigger fires; skip them
   only if you have deliberately decided not to use that trigger (see
   "Known limits" below).

2. Give the project a `CLAUDE.md` that reads `ORCHESTRATOR.md`. Either paste
   `ORCHESTRATOR.md`'s content directly into `CLAUDE.md`, or, to keep the two
   files separate and updatable independently, create `CLAUDE.md` with a
   single line:

   ```
   Read ORCHESTRATOR.md before delegating any task.
   ```

   A session only reads `ORCHESTRATOR.md` if something points it there; the
   pointer line is what makes that automatic. If the project already has a
   `CLAUDE.md` for other purposes, add the line to it rather than replacing
   the file (see "Install into an existing project" below).

3. Run the preflight check from the project root:

   ```bash
   python3 preflight.py
   ```

   It checks every row of the settings table further down except organisation
   effort limits, which needs an administrator to confirm. Fix anything it
   reports `FAIL` before proceeding; a `WARN` is informational.

4. **Restart Claude Code.** A worker definition added to `.claude/agents/`
   before your session started is not picked up by that session no matter how
   long you wait (confirmed empirically, `docs/FINDINGS.md`). Since this is a
   brand-new `.claude/agents/` directory, every session open at install time
   needs a restart to see it. Start a fresh session in the project after
   restarting.

5. Verify the install (see "Verifying it works" below) before delegating real
   work through it.

## Install into an existing project

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

3. Copy `dist/tools/*.py` into `$CONSUMER/tools/` and `dist/src/System/`
   into `$CONSUMER/src/System/` (or your chosen alternative location from
   the check above), the same commands as step 1 of a new install.

4. Add the line `Read ORCHESTRATOR.md before delegating any task.` to the
   existing `CLAUDE.md` rather than replacing the file. Where you add it
   matters less than that it is present; a natural place is near the top,
   beside any other file the project's `CLAUDE.md` already tells a session to
   read first.

   If `CLAUDE.md` already contains routing or delegation instructions from
   something else, decide whether they conflict before adding this bundle's:
   this bundle's routing table is meant to be the single source of truth for
   which worker to spawn (`src/ROUTING.md`'s own "Critical: this file does
   not route" section explains why a second, competing set of rules is worse
   than none).

5. Run `python3 preflight.py` from the project root, same as a new install.

6. Restart Claude Code **only if `.claude/agents/` did not already exist**
   before this session started. If the directory already existed (which it
   will, for most existing projects that already delegate to any subagent),
   the fifteen new definitions are picked up without a restart, typically
   within a turn or two. If you are not sure whether the directory predates
   your current session, restart anyway; it costs a few seconds and removes
   the question.

7. Verify the install before delegating real work through it.

## Verifying it works

Three checks, cheapest first:

1. **`/workers`** (this bundle's own status command): lists all fifteen
   definitions and confirms they loaded. If it reports fewer than fifteen,
   `.claude/agents/` is missing files or a restart is still needed.
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
| Organisation effort limits | check with your admin | Enterprise roles can cap effort per model. A capped level runs at the cap, silently under `json` output or in background agents. |

## Upgrading to a newer bundle version

Repeat the install steps for whichever case (new or existing project)
matches how this bundle got there originally: copy the new `dist/.claude/`
contents and `ORCHESTRATOR.md`/`preflight.py` over the old ones (they are
meant to be overwritten wholesale, not diffed by hand), re-run
`python3 preflight.py`, and restart only if `.claude/agents/` did not exist
before the current session. Compare the old and new `ORCHESTRATOR_VERSION`
values so you know what changed; the source repository's `docs/DECISIONS.md`
explains why, keyed by the commit named in the version string.

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
- Routing is a judgement made by a model reading a rubric, not a deterministic
  classifier. Expect to tune the table against your own task mix rather than
  trusting it out of the box.
- The routing table shipped with this bundle has one destination
  (`worker-sonnet-low`) plus two escalation triggers, one measured on a
  falsified-constraint shape and one an unmeasured safety-net policy for a
  frontier problem where every cheaper cell has already failed
  (`src/ROUTING.md` sections 2 and 4). It was tuned against this
  repository's own benchmark tasks, not yours; treat it as a starting point
  and watch for a task class it routes wrongly on your own work.
- The falsified-constraint trigger costs roughly USD 2.5 to 3.5 per fire,
  since it runs the Controller (a multi-role state machine, several
  `claude -p` calls) rather than a single worker. It fires rarely, only on
  that one specific shape, but the orchestrator session pays for the
  `claude -p` calls it makes directly with the Bash tool the same way any
  other spend is billed; there is no separate approval gate on it beyond
  what `ORCHESTRATOR.md` itself states. If you would rather this trigger
  never spends without a human confirming first, edit `src/ROUTING.md`
  section 4 to ask before running the Controller, or remove that step and
  fall straight through to `worker-opus-high`.
