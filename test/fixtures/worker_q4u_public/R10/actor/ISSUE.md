# Calculate invoice tax once on the subtotal

Amounts are integer cents and tax rates are integer basis points. Compute tax
as `(subtotal_cents * rate_basis_points / 10000)` rounded half up to the next
cent, using integer arithmetic. An invoice's tax is calculated once on the
sum of its line net amounts, not separately on each line. Return the subtotal
plus that tax. This matters for many small lines, where line-by-line rounding
changes the result.

Fix `billing/tax.py` and `billing/invoice.py` as needed. Run
`python3 -B public_check.py`, then check half-cent and split-line examples.
Do not edit the issue, public check, acceptance metadata or licence.
