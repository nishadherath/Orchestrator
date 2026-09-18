# Controller routing Stage R2: complete cell registry

Date: 2026-09-18. Branch: `v1.0-rc1`. Baseline HEAD: `1eb0fbe`.

## Result

One versioned registry now resolves all 15 Sonnet, Opus and Fable worker cells
across low, medium, high, xhigh and max effort. The live worker adapter,
offline evaluator, Controller standard profile and operational diagnostics use
the same resolver. The qualified router remains B0.

## Registry contract

`src/model_registry.json` records:

- the complete 3 by 5 logical cell matrix;
- exact CLI and expected served-model identifiers;
- supported efforts, context limit and explicitly unknown output limits;
- observed or configured-unverified availability and identity evidence;
- explicitly unknown provider token prices where no bound snapshot exists;
- direct-worker and Controller-role eligibility;
- offline wiring qualification, kept separate from unmeasured live quality;
- `standard` and `frontier-candidate` Controller role profiles.

`tools/model_registry.py` validates the whole registry before resolving any
cell. Unknown cells, incomplete matrices, invalid profiles and max-effort
Generator assignments fail visibly. Exact served identity is required; aliases
and silent substitutions are not accepted. Per-run projections reuse
`src/cost_table.json`; absent or null measurements stay unknown rather than
becoming zero or an invented estimate.

## Profiles

The Controller's executable standard profile remains behaviourally unchanged:
Sonnet-low Controller classification, Opus-high framing, Sonnet-medium
verification, Sonnet-high generation, Opus-medium critique and Sonnet-medium
selection.

The unqualified frontier candidate is now representable without hard-coded
fallbacks. It uses all three model families and, across its roles, all five
effort levels. Its Generator set contains Sonnet-high, Opus-xhigh and
Fable-high. Fable-max is reserved for Critic rather than Generator, preserving
the documented Generator max constraint. R2 does not make this profile
operator-selectable or automatic.

## Evidence

`test/harness/model_registry_tests.py` has eight offline tests. They verify:

1. the exact 15-cell matrix;
2. exact fake dispatch commands for all cells;
3. explicit Fable identity and rejection of Sonnet substitution;
4. evaluator identity resolution for every cell;
5. standard profile parity and frontier coverage of every model and effort;
6. known measured projection versus unknown Fable cost;
7. exact diagnostic model and effort comparison;
8. visible failure for unsupported cells and profiles.

The live worker adapter suite also pins `worker-fable-max` to
`claude-fable-5-1` with max effort. Offline live-worker and episode-runner
qualification evidence was regenerated against the changed implementations;
both report zero model calls and valid digests.

## Packaging and limits

The redistributable includes the registry JSON and resolver. Preflight treats
either as a required Controller dependency and uses exact identity comparison
in operational diagnostics.

R2 proves configuration and fake-provider wiring only. Fable's configured
identifier, availability, token prices, effort delivery, quality and latency
are not live-qualified. Those facts remain visibly unverified until the paid
identity and cell screen in R5. Role-profile selection and durable operator
controls belong to R3-R4.

## Validation

Final results: registry 8/8, live worker 6/6, episode runner 5/5,
diagnostics 4/4, historical Controller routing 6/6 and Controller self-test
12/12. The redistributable build completed at
`2026-09-18-1eb0fbe-dirty`; all 63 planned bundle files matched source. The
post-build offline harness passed 54/54 checks, including `CTRL-R2`, all 24
real-world graders, installer lifecycle and release parity. Graft deep rebuild
completed with 2,121 nodes, 4,258 edges, 421 file cards, 50 semantic summaries
computed, 2,071 cached, zero stale and zero pending. No provider model calls
were made.
