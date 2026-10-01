# Search results lag authoritative row revisions

A search index can trail an authoritative record after an update or deletion.
For a requested key, return the latest authoritative row revision; a latest
tombstone means the key is absent. Preserve the fast, unchanged case and do
not resurrect a deleted record from a stale index entry. The adapter and
public smoke check are fixed. Report what you verified and the next replay
check in `report.json`.
