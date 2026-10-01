# X5 v6 development candidate: consequential executable tasks

Date: 2026-09-29 Australia/Sydney. Status: routing screen passed. The pre-paid design below is preserved; see
`controller-x5-v6-screen-2026-09-29.md`. No pilot call has been made. B0 remains the shipping default.
The v5 first-miss stop and all used roots remain immutable.

## Diagnosis and change

V5's payment and feature screens froze automatic Controller decisions, but the
lease screen froze a worker decision. The public assessor recognised uncertainty
and material alternatives; it judged the lease effect recoverable and local.
That agrees with the actor's in-memory lease effect. This is a task construction
miss, not evidence to relax the rigour policy. The unassessed monetary case also
models only two local totals and does not stand as a consequential service task.

V6 retains the payment and feature actor and protected-oracle byte sets from v4.
It replaces lease and money with two new X5-only actors. Shipment commitment
models available stock, held orders and carrier-accepted dispatches. Its public
trace reproduces both an oversold reservation and a duplicate carrier commit.
A stock-only repair leaves the duplicate handoff. Migration restart models the
durable customer target and checkpoint read by billing exports. Its public trace
reproduces a row skipped after a crash and an older source row overwriting a
newer target. A checkpoint-only repair leaves the version regression. The issue
for each task states a real downstream effect and an authorised outcome while
leaving multiple causes open to investigation. The source comments describe
interfaces, without announcing a fault.

The two new actor packages contain only app.py, the editable service module,
public_check.py, issue.md, trace.json, acceptance.json and report.json. Their
protected reference and six weighted behavioural checks are under test/oracles.
The independent score rubric remains M/E/D/N/H 40/25/15/10/10 with critical
veto, false-success detection and verified probes. The existing payment and
feature packages and the X3 N01-D1 ordinary and C08-D2 clarification controls
are unchanged.

## Prospective gate

The six assessments are ordered X5-SHIP, X5-MIGRATE, X5-PAY, X5-FEAT, N01-D1,
C08-D2. New cases go first so a construction miss stops before repeating two
known development cases. Each has one fresh single-use N1 root and USD 0.50
assessment allowance. Only four frozen automatic Controller decisions followed
by one worker and one clarification may open the B/S/A pilot. The screen never
makes a worker or Controller role call. A settled miss, unresolved charge,
unqualified host or incomplete decision stops it. The v6 pilot protocol binds
six tasks, B/S/A arms, 18 matched episodes, protected scoring and a stop on an
unqualified host, unresolved charge or failed required admission. Pilot spend
requires a separate notice and manifest after the screen gate.

The screen ceiling is USD 3 local, distinct from expected provider spend. Based
on v5's three settled public assessments (USD 0.0615 to 0.0709 each), the six
v6 calls are expected to cost roughly USD 0.3 to 0.8 API-equivalent with prompt
length and caching uncertainty. The USD 144 pilot local ceiling and historical
USD 5 to 30 API-equivalent projection are separate. No v6 paid call is made
until the frozen manifest, full offline harness and dated cost notice are in
place. Standing project authorisation covers paid project calls below USD 100.

## Provider-free evidence and limits

The v6 audit reproduced both public traces; both baseline public checks passed.
All six protected checks per case passed against the reference. Both plausible
partial repairs passed the visible check but failed protected acceptance. A
label-only report and a partial repair falsely claiming completion were rejected.
The isolated WSL grader accepted both references at 100/100 and rejected both
baselines and partial repairs. The WSL actor probes denied direct oracle reads,
repository and Windows mount access, protected file writes and Graft escape;
all 14 checks per case passed with zero provider calls. The six public packets
and first-miss/durable-decision gates passed three tests. Evidence is in
`test/results/2026-09-29-controller-x5-v6-audit.json` and the direct tool
records. The full offline harness passed 82/82 checks, the manifest was frozen and
the six-call public screen passed its predeclared routing gate. See the
separate screen result for receipts and limits.

These are deliberately synthetic development tasks. Their output models
carrier commitments and durable target records, but no physical shipment or
production billing export occurred. A favourable route is not a measured
quality gain. The reserved X6 cases remain unseen; v6 is tuning-informed
development evidence.
