# Ledger and statement totals disagree at cent boundaries

The ledger rounds each entry before summing, while the statement sums binary
floats. Their totals diverge on fractional-cent charges and refunds. The
shared rule is to parse decimal amounts exactly, sum unrounded values, then
round the final total to cents using half-even. Repair the editable modules so
both consumers return the same two-decimal string. Preserve the adapter and
public check. Submit `report.json` with causal observations and a safe step
before posting corrected totals.
