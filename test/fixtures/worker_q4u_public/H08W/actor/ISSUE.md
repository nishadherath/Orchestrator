# Reconcile versioned events without stale resurrection

`apply_events(state, events)` receives a mapping from object ID to
`(revision, payload)` and ordered events of `(object_id, revision, operation,
payload)`. `operation` is `put` or `delete`. Ignore an event whose revision is
not strictly newer than the stored revision for that object. A delete must
retain its revision as a tombstone with `None` payload, so a later stale put
cannot resurrect the object. Return a fresh state mapping without mutating
the input. Ordinary newer puts must still work.

Only `reconcile.py` may change. Run `python3 -B public_check.py` and add your
own out-of-order and delete/resurrection checks. Do not edit the issue,
public check, acceptance metadata or licence.
