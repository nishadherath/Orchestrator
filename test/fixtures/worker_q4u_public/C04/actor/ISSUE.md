# Check Unicode label normalisation

A report claims equivalent Unicode labels can produce different lookup keys.
Verify `normalise_label()` against the stated contract: apply Unicode NFKC
normalisation, then Unicode case folding, then collapse every run of Unicode
whitespace to one ASCII space and strip the ends. Preserve other characters.
The result must be deterministic for the same input and reject non-strings
with `TypeError`.

Run `python3 -B public_check.py` and inspect meaningful edge cases. Change
`labels.py` only if a concrete counterexample requires it. If the
implementation already satisfies the contract, report that and leave it
unchanged. Do not edit this issue, tests, acceptance metadata or licence.
