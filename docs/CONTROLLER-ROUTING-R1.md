# Controller routing Stage R1: integrity boundary

Date: 2026-09-18. Branch: `v1.0-rc1`. Baseline HEAD: `1eb0fbe`.

## Result

The direct Controller now defaults to `integrity-v1`. This stage does not
change the qualified B0 router and does not automatically invoke the
Controller. It makes a manually or experimentally invoked Controller safer and
produces a bounded handoff for later routing work.

## Enforced behaviour

- An acceptance-v2 contract supplied with `--acceptance-contract` is validated,
  hashed and frozen before the first role call. Without one, the first valid
  Frame criteria are frozen as `framer-provisional` and cannot claim
  `verified-ready`.
- An unstable Controller classification closes with a gap before technique
  selection or candidate generation.
- Every candidate, including B0, needs exactly one critique. Integrity-v1
  rejects non-passing or derivable candidates, stale generated candidates,
  stale B0 pointers, unresolved load-bearing ledger premises, unverified
  introduced premises and Selector exclusions.
- The Selector runs before the winner is chosen. Code follows its rank order
  only among eligible candidates. B0 is a fallback only when it is current,
  passing and not excluded. An empty eligible set returns a gap.
- Reframes cannot change frozen acceptance criteria.
- Every normal close writes `controller-evidence.json`. The packet binds the
  task, acceptance, input identity, findings, rejected candidates,
  uncertainties, artefact hashes, outcome, readiness and accounting. Its
  schema, digest, path boundary and readiness cross-fields are validated before
  the run is reported complete.
- `legacy-quick-v0` retains the pre-R1 stability and first-survivor rules for
  exact historical comparisons. It must be selected explicitly.

## Evidence

`test/harness/controller_integrity_tests.py` contains ten offline adversarial
tests:

1. false stability stops before generation and preserves a useful gap packet;
2. incomplete critique coverage stops before selection;
3. Selector exclusions cannot be ignored;
4. a reframe cannot change externally frozen acceptance;
5. external acceptance plus a qualifying result produces verified-ready guidance;
6. an unverified introduced premise is ineligible;
7. stale selection and stale B0 are rejected;
8. a current passing B0 remains a valid fallback;
9. acceptance and packet digest tampering are rejected;
10. evidence packet schema and relative-path boundaries are enforced.

Historical characterisations in
`test/harness/controller_routing_r0_tests.py` now name
`legacy-quick-v0`. `tools/system_controller.py --selftest` still covers its
twelve state-machine and recovery scenarios. `test/harness/check.py` runs all
three suites as `SYSTEM`, `CTRL-R0` and `CTRL-R1`.

## Packaging

The redistributable includes `tools/controller_integrity.py`, the updated
Controller, `ControllerEvidencePacket.schema.json`, the schema documentation
and the maintained Controller guide. `tools/build_dist.py` and the bundle
manifest keep source and distribution hashes aligned.

## Limits

- A Controller `solution` is guidance; quick mode still does not implement or
  externally accept a repository change.
- `verified-ready` means the Controller packet is ready for a worker under an
  externally supplied contract. It does not mean that worker implementation
  has passed final acceptance.
- The qualified router remains B0. Automatic `auto/on/off` routing, model-cell
  registry work and worker handoff belong to R2-R4.
- This stage used no provider calls and makes no claim about live Controller
  quality, latency or cost.

## Validation

Final results: Controller integrity 10/10, R0 historical contracts 6/6 and
Controller self-test 12/12. The redistributable build completed at
`2026-09-18-1eb0fbe-dirty`; all 61 planned bundle files matched source. The
post-build offline harness passed 53/53 checks, including the 24 real-world
graders, installer lifecycle and release parity. Graft deep rebuild completed
with 2,096 nodes, 4,193 edges, 419 file cards, 50 semantic summaries computed,
2,046 cached, zero stale and zero pending. No provider model calls were made.
