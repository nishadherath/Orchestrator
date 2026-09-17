# Resolve the incident without changing working source behaviour

The source contract already passes. Determine whether the incident comes from
stale generated output or an incorrect invocation, and return the corresponding
operational action. Recommend a source patch only when source behaviour fails.
Change only `operations/diagnose.py`.

Run `python -m unittest discover -s public_checks -v` from the repository root.
