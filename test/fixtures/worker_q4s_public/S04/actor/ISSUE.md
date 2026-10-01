# Stable, constructor-based pickle reduction

Pickling a sorted collection should reconstruct it from its values and
public key function, not from private index and load-factor state.
`SortedList` and `SortedKeyList` in `sortedlist.py`, `SortedDict` in
`sorteddict.py` and `SortedSet` in `sortedset.py` must uphold the same
constructor-based reduction invariant. A round trip must preserve values,
ordering and key behaviour, including collections that have been mutated.

Run `python3 -B public_check.py`. Source edits are limited to
`sortedcontainers/sortedlist.py`, `sortedcontainers/sorteddict.py`,
`sortedcontainers/sortedset.py`. Do not edit the issue, public check,
acceptance contract or licence.
