# X5 v7 continuation preflight

Date: 2026-09-29 Australia/Sydney. Status: **frozen preflight; v7 pilot
completed under explicit approval**. See
`controller-x5-v7-result-2026-09-29.md` for the outcome.
The v6 pilot stopped after six settled episodes at USD 4.129411806. Its
runtime archive and six result hashes are preserved. The v7 continuation
uses the same six-task public screen and actor packages, but starts fresh
roots only for the four unrun task families at schedule positions 7-18.

The replacement grader was run provider-free on the six stopped actor
outputs: all six were functionally accepted by isolated host checks and
scored 100/100 secondary quality, compared with their frozen v6 published
50/100 scores. This is post hoc diagnostic evidence, not a change to the
historical receipts. A protected baseline, reference and plausible wrong
repair test passed for each new case: the correct repair with an honest
unverified report was functionally accepted, while a wrong repair claiming
completion was rejected and flagged. The continuation schedule, cost
notice, no-replay, over-budget stop, report-claim and causal-evidence tests
passed 6/6.

The provider-free manifest dry-run validated the stopped receipts and actor
hashes, the screen archive, current runtime package and host identity. It
reported 12 episodes, an USD 60 aggregate cap and 1,289 runtime files.
The full offline harness rerun passed 82/82 checks with zero failures at
Git revision `15ecf66`. The command was `python -B test/harness/check.py`.
The manifest is frozen at
`ea3bc5f689d1b55c72137d5424e5e6d0672ef4b19e741a92207e5c8ad29ad8c7`.
Its 1,289-file runtime archive at
`/var/lib/orchestrator-worker-n4/archives/x5-v7-pilot-ea3bc5f689d1`
matched inventory SHA-256
`527519ef4634ab043616e63e044a325c8e248a4eedcbd6d18d4acd6a37161b4e`.
The dated USD 60 cost notice is
`test/results/2026-09-29-controller-x5-v7-pilot-notice.json`.

The first root preparation attempt stopped before creating the v7 run
directory because both WSL user and root-store Claude.ai access tokens had
expired. The account sign-in completed and the checked credential sync helper
passed its backup and ACL checks. Provider-free preparation then created all
12 isolated roots, bound to the frozen manifest, with zero provider calls.
The preparation record is
`test/results/2026-09-29-controller-x5-v7-pilot-run/prepared.json`.

Automatic approval review rejected the first paid v7 episode before launch:
the user's earlier approval covered the stopped v6 pilot, while this USD 60
continuation was a new spend scope. The operator then explicitly approved the
separate v7 continuation. All 12 episodes subsequently completed and settled.

The historical first six and prospective next 12 will be analysed with
provenance shown for every task pair. The continuation is development
evidence, not an independent replication. The USD 60 local ceiling is
below `CLAUDE.md`'s USD 100 approval threshold. The approval review still
required explicit approval for this new spend scope, which was received.
Based on the six measured v6 episodes,
approximately USD 6-20 API-equivalent is projected for the 12 new
episodes, with Controller and host uncertainty. The cap is a safety bound.
The measured v7 spend was USD 3.020660704. This paragraph records the
preflight forecast and approval basis, not a replacement for the receipts.
