# X5 H03: isolated Controller acceptance regression

Date: 2026-09-30 Australia/Sydney. Status: **frozen provider-free
development case; no H03 provider call, paid admission or uplift claim**.
B0 remains the shipping default. H03 is a retrospective reconstruction of
the real acceptance-contract failure observed in H02, not a blind upstream
issue or a reserved X6 unit.

## Public task and prospective risk

The actor contains an isolated pre-repair Controller bundle, a short issue
and `public_check.py`. Only `tools/system_controller.py` is editable. Its
52 public files total 879,471 bytes. The issue reports a gap before later
Controller stages on a caller-supplied immutable acceptance contract, despite
a scripted corrective reply within the existing call ceiling. The public
check exercises an initially altered Framer reply and requires a completed
run with the external criterion unchanged in every committed frame. It does
not invoke a provider.

The frozen public risk finding is source-cited in
`test/fixtures/controller_x5_h03/catalogue.json` (digest
`92e333e2dfa2d493e653a778ecd37a93aa0746aa322d50965cfcab24ed5700ea`).
The actor source has separate initial, verification re-entry and critique
re-entry Framer paths. The public check perturbs only the initial reply.
The Scribe can commit batch members before a later acceptance check fails.
Thus an initial-only repair can pass public while leaving a consequential
re-entry or partial-commit failure. The private oracle checks both re-entry
paths. The separate public follow-up below checks critique re-entry only.
A no-external-contract
control is ineligible for review; a request to change criteria without an
authoritative new contract needs clarification. These controls test the
selection rule offline, not a production false-review rate.

A separate public follow-up, `risk_check.py`, was frozen before any H03
model call in risk manifest
`e01d9ae066e67bde6f01bb71f8c609581ba70a5ef38a5fdc00f6463748277fff`.
It exercises one **correctable** critique re-entry, distinct from the
private oracle's persistent-mismatch check. It is outside the actor during
the producer call. After a settled public success, the host can run it on
accepted bytes. On both Windows and WSL, it failed for the baseline and
public-passing partial repair, and passed for both complete repairs. A pass
closes the case before S/A; a qualified failure supplies identical public
evidence to both review arms. This check is an entry gate, not a protected
score.

## Protected calibration

The private `oracle.py` remains outside the actor. It checks initial
correction, verification re-entry correction, persistent initial mismatch,
persistent verification mismatch, persistent critique mismatch and an
ordinary run. It treats any committed record from a rejected Framer batch
as a critical error. The actor does not contain the oracle, variants or
fixture generator. On both Windows Python 3.12.14 and WSL worker Python
3.14.7, the same fake-role probes produced:

| Source | Public check | Protected score | Critical error |
| --- | --- | ---: | --- |
| Pre-repair baseline | Fail | 10/100 | Yes |
| Initial-frame-only partial repair | Pass | 45/100 | Yes |
| Existing-Scribe-retry alternative | Pass | 100/100 | No |
| Full pre-commit reference | Pass | 100/100 | No |

The machine records are
`test/results/2026-09-30-controller-x5-h03-probe.json` and its
`-wsl-probe.json` peer. The focused H03 fixture suite passed 3/3 and is
registered in the offline harness. No result has been obtained from a
model. The complete repairs are source-level alternatives for calibration;
their success is not evidence that either worker arm would produce them.

## Integration finding

Auditing the actor's Framer paths exposed a third path in the production
Controller: critique-triggered re-entry still committed a mismatched frame
before checking the frozen criteria. The production pre-commit guard now
covers all three call sites. A new integrity regression verifies that a
persistent critique mismatch gets two bounded Framer attempts and leaves
only the two prior valid frames in the ledger. The focused integrity suite
passed 13/13. This repair was discovered after H02 settled and does not
change its immutable scores.

## Admission boundary and next work

The case is suitable for a **development feasibility screen** only. Its
retrospective selection and single-case size cannot estimate population
uplift or justify X6. A fair paid comparison would need a fresh single-use
producer root, an exact notice for the H03 payload and cap, a public-only
entry decision, identical accepted S/A bytes, a source-cited review goal,
terminal receipts and a sealed protected grade. If the producer resolves
the public risk fully, stop before S/A. If it fails the public check, use
the separately frozen first-failure rule; do not convert it after seeing
the outcome. No root or approval from H02, K01 or K02 can be reused.

The checked distribution build and final full offline harness passed 83/83
after the third-path repair. The harness machine result is
`test/results/2026-09-30-controller-x5-h03-postbuild-harness.json`. Before
any paid dispatch, inspect H03 payload and
isolation from WSL, freeze the exact runner, analysis and dated cost notice,
and verify the actor catalogue again. A favourable development result would
still require a separately designed prospective multi-case and reserved
comparison before changing the default.
