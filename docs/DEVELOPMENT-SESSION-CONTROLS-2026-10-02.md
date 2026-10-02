# Development session controls and parallel execution

Observed tool contract: 2026-10-02, Codex desktop, Orchestrator project.
This is a capability record and proposed operating procedure. No launch was
performed to test it. The user expressly asked whether automation was possible
and requested a manual staged plan, not an automatic launch.

## Direct answer

Yes. The tools exposed to this session can create a new Codex chat with an
explicit supported model and reasoning effort, supplying a prompt that names a
validated project handoff. They can also launch and coordinate subagents with
explicit settings. These are capabilities available on this host, subject to
permissions, account access and runtime availability. They do not establish that
a requested launch has succeeded before its result is observed.

There is no exposed direct setter for changing this active turn's own model and
effort in place. Manual selection remains the route for that change. Creating
another chat or launching a subagent does not change the parent chat's setting.

## Exposed controls

| Operation | Available control | Boundaries |
| :--- | :--- | :--- |
| Fresh user-visible chat | `mcp__codex_app__create_thread` with `model`, `thinking`, project target and handoff prompt | Requires an explicit request for a new chat. A specific model override needs the user's explicit model selection. Discover the saved project first. |
| Subtask in this chat | `collaboration.spawn_agent` with `model`, `reasoning_effort`, scoped message and handoff | Requires explicit authorisation for delegation. Overrides require explicit requested settings; use limited/no history when overriding. |
| Coordination | Collaboration messages, follow-up, status, wait and interruption | One lead owns integration; child completion is evidence to review, not automatic acceptance. |
| Continue another user chat | `mcp__codex_app__send_message_to_thread` | Requires human authorisation to message that chat. Another agent's request alone is insufficient. |
| Fork existing history | `mcp__codex_app__fork_thread` | No model/effort fields in the exposed fork contract. Do not imply a fork alone selects them. |

At observation, collaboration exposed four concurrency slots in the root agent
tree, including the lead. This permits up to three children concurrently. It is
not evidence of an account-wide four-chat limit, nor a guaranteed future limit.
Separate chat launches have their own availability and resource constraints.

Both recommended models, `gpt-6-astra` and `gpt-6.1-sol`, expose High and Extra
high through these host controls. Sol also exposes Medium. Host schemas are
the authority for accepted parameters; they do not reveal the model currently
executing this conversation or independently verify provider-side reasoning.

[Official subagent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents)
supports explicit model/effort selection and explains inheritance when settings
are omitted. This host's full-history collaboration fork inherits settings and
does not accept overrides; use `fork_turns="none"` or a limited history with the
handoff for an explicitly selected child. The narrower exposed host contract
governs execution here.

## Recommended parallel block

Follow the [offline qualification plan](OFFLINE-QUALIFICATION-IMPLEMENTATION-PLAN-2026-10-02.md).
Freeze O0 before parallel work. If the user later authorises this route and
its named model/effort choices, assign O1 evaluator, O2 admission/feedback and
O3 identity evidence to three Sol High subagents. The lead coordinates contract
questions and reviews outputs. O4 integration starts after all three gates pass;
O5 independent review follows the integrated freeze. Do not launch nested
delegation simply because another slot becomes available.

Children share a filesystem by default. Assign disjoint new modules and tests;
reserve shared runner wiring, harness registration, root documentation, Git
mutations and `dist/` generation to the lead. If an edit overlaps another owner,
stop that dependent edit and agree one owner. This is cooperative coordination,
not OS-enforced isolation. For stronger write isolation, prepare correctly bound
worktrees and transfer an explicit source snapshot; uncommitted changes are not
automatically copied. New-chat worktrees require the user's explicit request
under the exposed creation contract.

Use a validated handoff for every child, including same-model children, with
absolute repository root, exact source/contract version, allowed writes,
forbidden shared mutations, test command, acceptance IDs and evidence output.
Each child checks its own Graft access and root binding. A fresh context cannot
be assumed blind to protected data if shared filesystem access still permits it.
Research actor/oracle isolation must be enforced separately.

The lead rejects output that lacks the required tests or changes the contract.
Run final integration tests on the combined revision, then independent review
and closure. Parallelism can reduce the independent implementation interval;
it cannot guarantee identical quality or a fixed speedup. These gates preserve
the required acceptance standard and expose integration defects before use.

## How authorisation would work later

The default remains operator-selected stage handovers. A later instruction can
explicitly authorise the parallel O1-O3 subagents and the named Sol High setting,
or request a new O0 chat on Astra High. That avoids manually choosing each
child's settings while preserving the project's notification and handoff rules.
It does not authorise paid research, publication, or arbitrary future agents.

Before any authorised launch, save and check the handoff, notify the operator
of path, target settings, API-equivalent estimate and elapsed range, then launch.
Verify the returned identity/status; if a setting is unavailable, report it
instead of silently substituting. Account quotas, sign-in and approval failures
may still require human action. No background scheduler or continuing work after
this chat stops is implied by these tools.

The Claude Code worker names, routing assessment and Agent-tool invariants in
the repository describe that runtime. They cannot be passed as Codex worker
types or treated as proof of equivalent model classes. The OpenAI development
settings above do not alter the Anthropic model registry or shipping routing.
