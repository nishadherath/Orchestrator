# Release-candidate account model identity check, 2026-10-02

## Disposition

The authenticated operator's Claude.ai Max account returned the exact registered provider ID for both Sonnet and Opus. This verifies model identity for the observed account, host, Claude Code version, and tested effort settings. It is not a model-quality, routing-quality, or Controller qualification. Controller X5 continuation/uplift and the real-world policy pilot remain deferred.

## Observations

- Anthropic's current model pages identify `claude-sonnet-5-5` and `claude-opus-5-5` as active: [Sonnet 5.5](https://platform.claude.com/docs/en/models/sonnet-5-5/overview), [Opus 5.5](https://platform.claude.com/docs/en/models/opus-5-5/overview), and [model lifecycle](https://platform.claude.com/docs/en/about-claude/model-deprecations). The source registry already contained those IDs.
- `claude auth status` reports `authMethod=claude.ai` and `subscriptionType=max`. The local CLI was 2.1.273; Opus returned an explicit client-version rejection. Updating the local CLI succeeded and installed 2.1.287.
- On 2.1.287, a no-tool fixed-token Sonnet low probe returned `assistant.message.model=claude-sonnet-5-5`; an Opus high probe returned `assistant.message.model=claude-opus-5-5`. Both completed successfully. Neither probe included repository, issue, or policy-pilot data.
- Machine-readable stream and usage evidence: `test/results/2026-10-02-current-account-model-identity.json`. Paid-call notice and the cost correction: `test/results/2026-10-02-current-account-model-identity-notice.md`.
- Claude Code reported USD 1.197270 API-equivalent for Sonnet and USD 0.912204 for Opus. Two failed CLI attempts reported USD 0.001925 combined. Total reported API-equivalent is USD 2.111399. Auth is via Claude.ai Max, not an API key; the CLI did not provide an invoice amount. The initial USD 0.20 per-call / USD 0.40 combined estimate was wrong and not enforced.

## Inference and limits

The current registered Sonnet and Opus IDs are served for this account through Claude Code 2.1.287 at the tested effort levels. Other accounts and older CLI versions were not verified. The account check makes no claim about provider-served effort metadata, quality, latency, routing performance, or future model availability.

## RC status

This account check supplements the bounded RC evidence dated 2026-10-01. It does not change the supported B0 policy, Controller status, or pilot scope. The model registry continues to hold portable vendor-verified IDs; this operator-account observation is kept as dated local evidence, not copied into the consumer bundle.

## Current RC validation

- `tools/model_registry.py --check`: PASS, 16 cells and two role profiles.
- `tools/generate_workers.py --check --json`: PASS, zero drift across 16 generated workers.
- `tools/build_dist.py`: PASS after its complete offline gate; bundle stamp `2026-10-02-b0f4f65-dirty`.
- `test/harness/check.py --json` after rebuild: PASS, all reported checks passed.
- `test/results/2026-10-01-rc-freeze.py`: PASS. The [85-file bundle archive](../../test/results/2026-10-01-rc/orchestrator-rc-0b7d6c1e406500c4.zip) has SHA-256 `0b7d6c1e406500c412eaf01411838f48d32c518ffa5b30172347e212088339c2`; archived-input reproducibility, deterministic archive, clean install, upgrade, rollback, drift rejection, and preservation checks passed.
- `tools/evaluation_freeze.py --check`: PASS. Its candidate remains `paid_launch_ready=False`, because the working source is dirty and the separate policy pilot is deferred.
- `tools/release_check.py --json`: mechanical PASS, no failures. `LICENSE` and sensitive-material checks pass. The only operator actions are a clean build stamp and publication.

This is a validated, unpublished RC candidate. It is not a clean-source release build: no commit or publication was made. The release checker correctly retains those two operator actions.
