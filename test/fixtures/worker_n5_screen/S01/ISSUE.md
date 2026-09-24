Implement `solve(data)` in `app.py` for a service port setting. Accept an
integer or a string containing a decimal integer with surrounding whitespace.
Ports 1 through 65535 are valid. Reject booleans, missing values, blank or
non-decimal strings, and out-of-range values. Return
`{"port": number, "error": null}` for a valid setting or
`{"port": null, "error": "invalid_port"}` otherwise. Keep the JSON-line CLI.
