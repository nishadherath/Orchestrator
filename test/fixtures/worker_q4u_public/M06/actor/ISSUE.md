# Decide whether naive timestamps can be migrated to UTC

The request says: "Convert these local event times to UTC for import."
The supplied rows contain naive timestamps such as `2026-10-04 02:30:00`.
`migration.py` requires an IANA timezone identifier to interpret local time;
the request supplies none. An offset or the current host timezone is not a
safe substitute. The request also leaves unspecified how to handle nonexistent
or repeated wall-clock times at daylight-saving transitions. Do not invent a
timezone or a resolution policy, and do not change the migration code until
both are clarified.

Complete the empty `decision.json` placeholder with keys `status`, `missing_fields`, and `rationale`.
`status` must be `needs_input` or `ready`. `missing_fields` is a list of stable
names for the inputs or decisions still required; `rationale` is a short
explanation.
Run `python3 -B public_check.py`. Only `decision.json` may be
changed; leave the source, issue, check, metadata and licence untouched.
