# X5 v6 pilot preflight

Date: 2026-09-29 Australia/Sydney. Status: **historical preflight**. The
operator approved this frozen pilot, which later stopped after six episodes.
See `controller-x5-v6-pilot-stop-2026-09-29.md` for the outcome. The
preflight evidence below describes the state before any pilot call.

## Frozen comparison

The six-task public screen passed its prospective routing gate with six
settled assessments costing USD 0.338381801. No worker or Controller pilot
episode ran in that screen. Its result is
`test/results/2026-09-29-controller-x5-v6-screen-results.json`.

The paired B/S/A pilot has 18 episodes across the same six actor packages.
The frozen pilot manifest is
`test/results/2026-09-29-controller-x5-v6-pilot-manifest.json`, SHA-256
`1a8eb29b2f2b816dafed0f6bbe22613cc496ee9601e55a37e1bb0822a8a001bf`.
The screen runtime archive was materialised and verified before the pilot
freeze. The pilot driver checks the screen result, runtime package and host
identity again before each episode.

## Provider-free checks

The independent X5 graders rejected the baseline and plausible incomplete
repairs, and accepted the protected references at 100/100. Actor isolation
denied protected oracle, sibling path, credential and Graft escapes. The two
X3 controls were graded against their existing protected oracle under the
isolated boundary. Pilot schedule, approval gate and no-replay tests passed
3/3. The pilot preparation created 18 private N1 roots and made zero provider
calls. A subsequent read-only check found all 18 roots ready with zero
unresolved charges.

The full offline harness rerun after pilot preparation passed 82/82 checks
with zero failures at Git revision `15ecf66`. The command was
`python -B test/harness/check.py`. The v6 pilot-specific provider-free tests
passed 3/3 separately. No pilot episode was started by either check.

## Spend gate and remaining work

Each episode has an USD 8 local cap; the aggregate ceiling is USD 144.
Historical X4/X5 calls suggest approximately USD 5 to 30 API-equivalent for
the whole pilot, but Controller and frontier paths make that range uncertain.
The local ceiling is a safety bound, not a forecast. `CLAUDE.md` requires
operator approval before a `claude -p` run above USD 100. The earlier USD 3
screen notice authorises no pilot episode. No pilot notice exists and no
pilot provider call has been made.

After explicit approval of this exact frozen pilot and USD 144 ceiling, the
driver will run episodes sequentially, stop on its predeclared admission,
identity, credential or accounting failures, grade worker output through the
protected boundary, and report paired quality, cost and elapsed time. The
development pilot cannot by itself promote a default: X6 reserved comparison
remains unseen. B0 remains the shipping default.
