# Decide whether a currency conversion is ready

The request says: "Convert the EUR invoice to USD for settlement." It gives
the invoice amount and both currencies, but no exchange-rate quote and no
timestamp at which a quote should apply. `conversion.py` accepts an explicit
rational quote; its result depends on that quote. A current website rate or
an arbitrary date would be an unjustified substitute. Do not run a conversion
or change the source until the quote and its as-of time are supplied.

Complete the empty `decision.json` placeholder with keys `status`, `missing_fields`, and `rationale`.
`status` must be `needs_input` or `ready`; `missing_fields` lists stable names
for the absent inputs or decisions; `rationale` briefly explains the stop.
Run `python3 -B public_check.py`. Only `decision.json` may be
changed; leave the source, issue, check, metadata and licence untouched.
