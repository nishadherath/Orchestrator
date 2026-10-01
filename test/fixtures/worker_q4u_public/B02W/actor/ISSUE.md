# Make JSON Lines relative seeking bounded and correct

`JSONLIterator` must terminate when a relative seek lands in the final
incomplete line and no later newline exists. A negative `rel_seek` must
select a position from the end instead of seeking past EOF. Keep ordinary
forward iteration and positive relative seeking intact. Only
`boltons/jsonutils.py` may change.

Run `python3 -B public_check.py`. The public check covers ordinary and positive seeking; add your own bounded checks for the two stated edge cases.
Do not edit this issue, public check, acceptance metadata or licence.
