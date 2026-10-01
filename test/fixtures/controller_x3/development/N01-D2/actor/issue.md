# Move the request timeout setting to seconds

The configuration contract now uses `request_deadline_s` (seconds) instead of
`http_timeout_ms` (milliseconds). Move the 750 ms default to 0.75 seconds and
update both the HTTP client and scheduler readers. Runtime overrides of the
new setting must work; remove the old key. Keep retry behaviour unchanged and
leave the JSON adapter and public smoke check intact. Report your observations
and a next check in `report.json`.
