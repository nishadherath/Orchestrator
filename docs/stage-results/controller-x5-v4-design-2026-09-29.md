# X5 v4 redesign: case qualification and stopped public screen

Date: 2026-09-29 Australia/Sydney. Status: **the prospective screen stopped
on its first task; X5 remains incomplete**. The operator selected redesign after the v3
four-of-four gate failed. V1-v3 and their cost records remain immutable. B0
remains the shipping default. V4 made one settled public assessment call and
no worker or Controller pilot call.

## Public cases and controls

Four new X5-only actors are under `test/fixtures/controller_x5_v4/`. Their
adapters accept one JSON request on stdin and emit one JSON result. Only the
case module and `report.json` are editable. The protected reference and
acceptance inputs live separately under `test/oracles/controller_x5_v4/`;
the actor packages contain no expected-output oracle.

| Proposed task | Public competing causes | Distinguishing observations | Different safe repairs |
| --- | --- | --- | --- |
| X5-PAY | Second purchase, lost committed receipt, tenant key collision | Response-loss retry and same key across tenants | Persist commit receipt before response; scope receipt identity by tenant; preserve conflict and abort semantics |
| X5-FEAT | Backend route, cache identity, stale update | Cold and warm tenant lookup plus update/read | Scope cache by tenant/feature; invalidate only the updated entry |
| X5-LEASE | Database saturation, worker clock, stale acknowledgement | Stable DB report, skewed clock and token transition | Decide expiry on server time; fence acknowledgements by token |
| X5-MONEY | Per-line rounding, binary aggregation, refund sign | Two fractional-cent samples with different consumer errors | Sum signed Decimal values exactly, then round once for both consumers |

The unchanged X3 development controls are N01-D1 (ordinary worker) and
C08-D2 (missing-decision clarification). C03-D2 remains a clear worker task
and is excluded. C01/C03/C04/C06/C07 original X3 actors and all reserved
tasks remain untouched. The v4 order is the four proposed suitable cases,
then N01-D1, then C08-D2. The new screen driver at
`tools/controller_x5_v4_screen.py` is separate from the frozen v3 driver
and refuses a later assessment when a prior settled decision misses its
predeclared action.

## Provider-free evidence

`tools/controller_x5_v4_audit.py` reproduces every public incident, checks
the public smoke test against baseline/reference/wrong variants, runs the
protected behaviour cases, and requires a verified two-probe report for a
completion claim. The result is
`test/results/2026-09-29-controller-x5-v4-audit.json`.

| Case | Baseline passes | Reference passes | Plausible partial repair passes | False full claims |
| --- | ---: | ---: | ---: | --- |
| Payment | 2/5 | 5/5 | 3/5 | rejected |
| Feature | 1/3 | 3/3 | 2/3 | rejected |
| Lease | 1/4 | 4/4 | 3/4 | rejected |
| Money | 0/4 | 4/4 | 3/4 | rejected |

All four public traces reproduced byte-equivalent structured output. This
establishes 16 local behavioural checks and source-hash records. The
independent acceptance compares behaviour, not a specific patch. The audit's
phrase scan checks for the earlier explicit diagnosis leakage; it cannot
prove that a human or model cannot infer a repair by reading the code.
All four actor packages passed the existing WSL namespace's 14 isolation
checks, including denied oracle reads, actor-only Graft retrieval and blocked
protected-file writes. The isolated executable grader rejected each baseline,
accepted each reference at 100/100, and flagged each plausible partial
repair's full claim as false success. Its source and final source hashes are
bound by the frozen manifest. The payment actor includes a deterministic
parallel-batch interleaving; real OS-thread contention remains untested.
The phrase scan and case construction were authored in this development
session. They are independent of the actor's public check, but are not a
blinded external review.

The v4 screen module parses on Windows and imports in the configured
`kali-linux` WSL host. A read-only WSL package call found six packages.
The Windows sandbox could not import its Unix `resource` dependency, and
ordinary sandboxed WSL enumeration returned access denied. An escalated
read-only host check succeeded. No host identity or served-effort claim was
inferred from that import.

## Frozen rules for the next screen

The public-selection gate is unchanged in strength: four actual automatic
Controller admissions, worker for N01-D1, clarification for C08-D2. One miss
stops before any pilot role or worker episode. Assessment is sequential,
one call per task, each in a fresh single-use root with USD 0.50 local cap;
the full six-call ceiling is USD 3. These are admission caps, not invoices.
Expected six-call API-equivalent spend based on v1/v3 receipts was USD
0.15-0.60; the dated notice capped all six calls at USD 3. Only the first
call occurred, costing USD 0.050811401 as recorded by the root ledger.

For later B/S/A grading, keep the existing evaluator's M/E/D/N/H weights
40/25/15/10/10. Each protected case's milestone weights sum to 100 and its
critical flags are in its `acceptance.json`. Critical error zeroes quality;
a full claim without independent acceptance is false success. A verified
partial result can retain milestone and evidence credit without being called
complete. A completion requires all behavioural checks, two distinct reproduced
discriminating probes, matched causal concepts and a case-specific safe
next step. Generic diagnosis and next-step labels are rejected as false
completion even when code behaviour passes. The 18-episode
pilot retains the separate USD 144 local ceiling and earlier USD 5-30
API-equivalent projection, with 2-8 hours serial runtime. It is not
authorised by a future screen result alone.

The assessment used frozen manifest
`test/results/2026-09-29-controller-x5-v4-screen-manifest-r2.json`, hash
`244ea833f2fb122b4937410b75239db08c9548846310a417563244ff2df9b7a4`.
The earlier `screen-manifest.json` hash was superseded before root preparation
because the full harness watchdogs changed; no assessment used it. WSL
validation matched the replacement's actor, protected oracle, runtime and
host hashes.
The generic host record matches v3, and seven relevant Q4R/launcher/registry
source hashes match the v3 receipt. That supports reuse of the settled
Sonnet High canary only if authentication and installed host settings
remain qualified immediately before launch.

The preassessment gates completed:

1. Interactive WSL Claude.ai sign-in completed. The checked sync helper
   promoted it to the private worker store and preserved the ignored backup's
   ACL. Root-store inspection passed; no credential value was printed.
2. The full Windows offline harness passed 82/82 checks after its X1 and
   X3/X4 aggregate watchdogs were increased to 900 and 600 seconds. Both
   suites passed unchanged assertions directly in 438 and 282 seconds.
3. The replacement source and host seal validated. A dated USD 3 notice
   bound to its hash preceded six fresh single-use root preparations.

`X5-PAY` settled one public assessment under its USD 0.50 allowance. The
provider reported `claude-sonnet-5`, one call, and USD 0.050811401; served
effort was not reported. The root ledger has no unresolved charge. The
assessment described an investigation but set `frame_confidence=uncertain`
and `failure_cause=identity`. The unchanged N3 selector stopped with
`unresolved_frame` before freezing a worker cell or making a Controller
routing decision. Its public evidence cited the issue, public check and
trace, but did not establish a resolved task frame. The screen's
first-miss rule left X5-FEAT, X5-LEASE, X5-MONEY, N01-D1 and C08-D2
unassessed. No pilot role or worker call ran. See
`test/results/2026-09-29-controller-x5-v4-screen-result-r2.json` and the
settled N1 root `7e2c255bcd9687d340d1eca2`.

The v3 canary's settled USD 0.2724994 and two assessments' USD 0.094155001
remain historical. V2's separate USD 1 local hold remains uncertain despite
the no-launch audit. V4's one assessment is a failed development screen,
not replication or quality uplift.
X5, X6, X7 and X8 remain incomplete.

## Verification and next action

Commands run in this session:

- `graft_check_freshness`: MCP worked; committed graph reported 20 changed
  indexed source files, 669 unindexed new files and stale semantic summaries.
  Scoped Graft queries returned source spans. This is index drift, not evidence
  that any v4 source is wrong.
- `controller_x5_v4_audit.py`: all four case audits passed, with zero provider
  calls; see machine-readable result.
- WSL `_packages(_rows())`: returned four new cases and two controls.
- Seven focused WSL screen/scoring tests passed. All four final actor
  isolation probes and all four isolated baseline/reference/wrong-repair
  grader probes passed with zero provider calls; see
  `test/results/2026-09-29-controller-x5-v4-isolated-evidence.json`.
- New X5 files: 43 Python/JSON/Markdown files passed syntax, JSON,
  LF and trailing-whitespace checks. The repository prose check passed
  829 files. Tracked status edits passed `git diff --check`.
- Full `test/harness/check.py`: two WSL attempts hit the X0 60-second
  aggregate timeout. An unrestricted Windows run reported 80 passes and
  watchdog failures for X1 and X3/X4. The direct unchanged suites passed
  12 tests in 438 seconds and 57 tests in 282 seconds. After increasing only
  their aggregate harness watchdogs, the complete Windows run passed 82/82.
- The refreshed WSL login sync and private-store inspection passed. The
  replacement manifest validated after the watchdog edit. Six roots were
  prepared, and the first public assessment settled with one reported call,
  USD 0.050811401 and no unresolved charge.

The v4 screen is stopped. The measured miss does not establish whether the
payment case would have routed to Controller after a resolved frame, nor
whether a Controller pilot would improve quality. Any further redesign needs
a new prospective candidate and fresh roots. Do not relabel this task,
relax the selector, replay its settled assessment or advance to the pilot.
