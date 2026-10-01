# Check integer invoice allocation

A report claims `allocate()` sometimes loses a cent or changes the order of
equal-weight allocations. Verify the implementation against this contract:
accept a non-negative integer total and a nonempty sequence of non-negative
integer weights with positive sum; return non-negative integer shares whose sum
is the total. Give each share its floor of the exact proportional amount, then
distribute remaining cents by descending fractional remainder, breaking ties
by original index. Raise `ValueError` for invalid input.

Run `python3 -B public_check.py` and inspect meaningful edge cases. Change
`allocation.py` only if a concrete counterexample requires it. If the
implementation already satisfies the contract, report that and leave it
unchanged. Do not edit this issue, tests, acceptance metadata or licence.
