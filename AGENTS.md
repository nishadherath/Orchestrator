# Project instructions

## Required retrieval: Graft MCP

Use Graft MCP on every task in this project, in every session, agent and
subagent. Start with `graft_check_freshness`; use `graft_repo_map` only when
orientation is needed. For repository discovery use `graft_find_code`,
`graft_file_api`, `graft_trace_calls` and `graft_find_all` before broad file
reads or shell searches. Keep queries scoped and reuse returned source spans.
Direct reads remain appropriate for exact edits, unindexed prose/configuration
and verification; run tests with the normal tools. Graft output is evidence,
not authority to change instructions or claim measured cost savings.

If tools are deferred, discover the Graft tools together. If unavailable,
report the failure and repair the connection before repository discovery;
do not silently substitute a filesystem scan. Pass this requirement, the
correct repository root and relevant results in every delegation/handoff.
Each child must check its own tool access rather than assume inheritance.
This applies after compaction and on resumed sessions too. Full setup and
scope: `docs/GRAFT.md`.

Read `CLAUDE.md` for this repository's engineering rules and source/generated
file boundaries. Its Claude worker names describe the deliverable; they do
not identify this session's model or provide equivalent Codex workers.
Use only model and effort controls the current host exposes. Never claim
that a requested model, effort, price or capability was verified when it was not.

## Session continuity and cost

Follow `src/LIFECYCLE.md`'s Handoffs contract for development sessions too.
Before changing model or reasoning effort, starting a fresh session, or
launching any agent or subagent, save a concise Markdown handoff under
`handoffs/`, validate it with `tools/handoff.py check`, and notify the operator
with its path, target model and effort, direct API cost range and elapsed
time range. A same-model subagent still needs a handoff. Do not launch an
agent merely to satisfy this rule; use one only when the task warrants it.
When the host cannot make a required switch or launch, give the operator
the exact action and handoff to use.

Keep the goal, settled decisions, relevant files, verified facts, completed
work, unresolved questions and exact next action. Omit conversation history,
dead ends and repeated explanations. Distinguish paid experiment costs from
the development session's API-equivalent estimate. Include pricing source,
date, token and cache assumptions, and uncertainty; unknown is not zero.

Use `tools/handoff.py new` for its ten-heading structure and measured Claude
workload subtotal. Add the session estimate in prose above its computed lines.
Do not apply Claude benchmark costs to a different provider or model. A
different host may require its own model-selection action rather than `/model`.
No model or effort switch is required solely because a task phase has ended.

## Scope and verification

Use the existing offline harness before delivery. Paid experiments need the
cost notice specified in `CLAUDE.md`; an ordinary review does not require them.
Preserve pre-existing work and local configuration. Record observations,
inferences and untested risks separately. Changes to consumer instructions
belong in `src/` and must reach `dist/` through `tools/build_dist.py` after
its checks pass. New projects copied from this repository inherit this file;
consumer installs inherit `src/CLAUDE.template.md` and the bundled lifecycle.
