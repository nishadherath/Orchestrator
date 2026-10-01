# X5 recovery R3: stopped after the first producer

Date: 2026-09-30 Australia/Sydney. R3 manifest:
`dbfb0b877f6696c74198efd4926f7eb5d049a1e0443b507d4ea4dad23327e1f5`.
The user approved a maximum of USD 5 per root and USD 30 for the campaign.
The projected API-equivalent total was USD 2–12, with subscription billing
potentially different.

## Observations

The WSL Claude.ai credential had expired before the first provider dispatch.
After a successful reauthentication, the guarded root credential store was
synced. No task root or charge had started before that sync.

R01 B0 made one provider call. Its terminal, writer-stopped receipt reports
`claude-sonnet-5`, valid identity and USD 0.16955 API-equivalent cost. Its
executor state was `accepted` after one attempt, with no unresolved charge or
budget breach. The host-run public check passed. The worker's report described
three source repairs but stated that it could only trace the public scenarios
manually because no execution tool was available in its session.

The protected grade, run after the public eligibility decision, was 85/100
and failed a critical replay case. Actor access to the protected oracle was
denied. This is a false public success, not a public recovery signal.

The frozen eligibility helper rejected R01 too early because it expected
`budget.unresolved is False`. The executor actually returns an empty list for
a settled root. Its test fixture repeated the wrong Boolean shape. The
original result remains in
`test/results/2026-09-29-controller-x5-recovery-feasibility-r3-run/R01-producer-result.json`.
After repairing the helper and test fixture, a provider-free reconciliation
of that same settled root returned `no publicly observable unresolved work`.
The reconciliation is recorded in
`test/results/2026-09-30-controller-x5-recovery-r3-reconciliation.json`.

## Decision and limits

R3 stopped after R01. No R01 S/A or R02 root started. The protocol repair
changes the frozen runtime package, so the manifest-bound R3 paid runner must
not be resumed or replayed. The sole measured R3 API-equivalent cost is USD
0.16955. There is no paired Controller effect estimate and no basis for X5
promotion. B0 remains the default; X6 reserved cases remain sealed.

The protected miss cannot be promoted into a retrospective trigger: the
Controller would have had only the passing public check and the worker's
completion report at the decision point. A next candidate needs a genuine
public failure or concrete partial claim before cloning. R02 is unrun, but
further paid execution requires a new frozen, checked runtime and notice.

## Verification

The repaired protocol's provider-free unit suite passed 4/4. A full harness
rerun in WSL exceeded its 60-second timeout inside the unrelated X0 test;
that same X0 suite passed 6/6 in 14.4 seconds with the bundled Windows Python.
The native full harness ran all 83 checks and passed 79. Four unrelated checks
failed on this host: two could not read WSL-root-protected historical Q4
result directories, the real-world CLI check failed under Windows, and the
compact benchmark self-test could not spawn a child process. Its JSON record
is `test/results/2026-09-30-controller-x5-recovery-r3-poststop-offline-harness.json`.
The same native full harness with elevated fixture access then passed 83/83
after the protocol repair; its JSON record is
`test/results/2026-09-30-controller-x5-recovery-r3-poststop-offline-harness-elevated.json`.
No post-stop provider call was made.
