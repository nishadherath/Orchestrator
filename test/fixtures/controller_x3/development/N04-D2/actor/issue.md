# Complete the staged signing-key rotation

The approved first stage of the rotation uses synthetic key identifiers `blue`
and `green`. During the overlap, verification must accept both identifiers,
signing must use `green`, and unknown identifiers must remain invalid. Do not
remove `blue` until the later receipt review. Follow this supplied procedure
and report what you verified and the next check in `report.json`.

The adapter and public smoke check are fixed. The identifiers are fixtures,
not credential values.
