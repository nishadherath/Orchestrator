# A report lookup can cross tenant ownership

The listing endpoint scopes reports to the requesting tenant, but a caller can
also look up a report by its object ID. An object ID is not proof of ownership.
Return a report only when it belongs to the requesting tenant; legitimate owners
must still be able to open archived reports by ID. Unknown IDs remain absent.

The fixed adapter and visible smoke check exercise the listing path. Repair
`reports.py`, then record the cause, two reproduced observations and a safe
next check in `report.json`.
