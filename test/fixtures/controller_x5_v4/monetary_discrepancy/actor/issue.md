# Ledger and statement disagree at cent boundaries

Two consumers disagree on fractional-cent inputs. Per-line rounding, binary
aggregation and refund sign handling are live explanations. Use trace.json
and a distinguishing probe before changing amounts.py.

The approved policy is to sum signed decimal text exactly and round the
final total once to cents with half-even. Both consumers return the same
two-decimal string. Negative values are refunds. Preserve the adapter and
public files. Submit report.json with observed probes, diagnosis, completion
claim and next verification step.
