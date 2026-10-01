# Handle absent profile data in the email adapter

The profile record may be `null` or may lack an `email` key. Return a JSON
`null` email in either case, while preserving valid email strings. Fix the
local adapter function. Do not change the JSON entrypoint or public check.
Record honest observations and a next check in `report.json`.
