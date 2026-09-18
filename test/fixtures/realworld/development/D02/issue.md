# Preserve the legacy timeout option

Rename `--request-timeout` to `--timeout` while keeping the old spelling for
the documented transition period. Reject conflicting values, emit a deprecation
warning for the old spelling, and keep both names in help output. Change only
`cli/options.py`.

Run `python -m unittest discover -s public_checks -v` from the repository root.
