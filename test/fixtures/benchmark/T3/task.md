Implement `parse_duration(text)` in `duration.py` to this contract. Do not
change `test_duration.py`.

A duration string is made of up to three components, in this fixed order:
an hour count, a minute count, a second count. Each present component is one
or more digits immediately followed by its unit letter, `h`, `m`, or `s`.
Any component may be omitted, but at least one must be present, and no unit
may repeat or appear out of order. There is no separator between components
and no whitespace anywhere in a valid string.

Examples of valid input: `"2h"`, `"30m"`, `"45s"`, `"1h30m"`, `"2h15m10s"`,
`"0h5m"`.

Examples of invalid input, each of which must raise `ValueError`: an empty
string, a bare number with no unit (`"30"`), an unknown unit (`"5d"`), units
out of order (`"30m1h"`), and a repeated unit (`"1h2h"`).

The return value is the total duration in whole seconds, as an integer.

When you are done, run this yourself and confirm it passes before reporting
back:

    python3 -m unittest discover -s . -p "test_*.py"
