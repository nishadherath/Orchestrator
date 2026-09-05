# Decision ledger

Append-only. One entry per decision, newest last. An entry records what was
decided, why, and what would reverse it. Do not edit earlier entries; add a
superseding entry instead.

## 2026-09-05 D1. Adopt the CLAUDE.md layout on disk

Decision: move the deliverables under `src/`, add `docs/`, `test/`, `tools/`
and `dist/`, and rename the consumer install guide from `README.md` (briefly
`PERSONA.md`) to `src/README.md`.

Why: `CLAUDE.md` described this layout while the tree was flat, so every path
in the charter was wrong. Moving `.claude/agents/` out of the repository root
also stops the fifteen workers loading into development sessions, which the
charter forbids outside the dogfooding protocol.

Reversal: none expected. `tools/` is an addition to the charter layout because
the generator and the bundle builder are neither deliverables nor tests.

## 2026-09-05 D2. Generated persona files stay at the root, without their generator

Decision: `ENGINEERING_PERSONA.*.md` and `ENGINEERING_PERSONA_LANGUAGES/` remain
at the repository root as copied-in generated artefacts. Their source
(`source/core.source.md`, `source/languages.source.md`) and builder
(`build_persona.py`) live in another repository and are not vendored here.

Why: the persona documents locate themselves at the root and the loading matrix
in section 3.2 depends on that. Vendoring the generator would duplicate a
build that has one owner elsewhere.

Guard: `test/harness/persona.sha256` records a hash of each file with carriage
returns stripped. The harness fails if a hash changes, so a hand edit of a
generated file is caught. To update: rebuild from source, copy in, run
`python3 test/harness/check.py --update-persona-manifest`, commit both.

Reversal: vendor the generator if the persona starts changing in step with this
repository.

## 2026-09-05 D3. Worker definitions are generated with the persona inlined

Decision: `src/agents/*.md` are produced by `tools/generate_workers.py` from
`src/WORKER_PERSONA.md` and the routing table in `src/ROUTING.md`. The shared
persona is inlined into each definition. A cell's `model-specific-*` section is
inlined only when non-empty. Each description states the cell, the assessments
that route to it (or that none do), and the instruction never to pass `model`.

Why: the hand-written definitions told each worker to read `WORKER_PERSONA.md`
by bare relative name, which fails when the definitions are installed globally,
and cost a tool call at startup to load an empty section. Descriptions are the
one field the orchestrator sees in the Agent tool listing without reading the
rubric; identical descriptions carried no information. Deriving the routed
assessments from the table keeps one source of truth.

Kept: all fifteen cells, because CLAUDE.md fixes the count. Six are not in the
routing table and their descriptions say so. Dropping them is a charter change.

Reversal: if the empirical checklist shows a worker benefits from knowing its
cell, fill the sections in; no generator change is needed.
