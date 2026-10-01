# Parsed requirements and markers do not survive serialisation

A build cache pickles parsed requirements and environment markers, then loads
them in another process. Round-tripping currently fails for some objects, and
older pickle state shapes need to remain loadable. Preserve parsed equality,
string representation and validation of malformed state while restoring
compatibility across the parser nodes, markers and requirements.

Run `python3 -B public_check.py`. Edit only `packaging/_parser.py`,
`packaging/markers.py` and `packaging/requirements.py`. The hidden checks
exercise several object and legacy-state shapes; no external dependencies
are required.
