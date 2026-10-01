# Controller closes before checking a supplied acceptance contract

An external caller supplies one immutable acceptance criterion for a quick
Controller run. A reproduced run closes with a gap before the later
verification and candidate stages, although the scripted roles include a
corrective reply within the configured call ceiling. Run
`python public_check.py` to reproduce the observed behaviour.

Make the Controller recover when the role output is correctable. Preserve
the caller's criterion exactly, keep the existing retry ceiling, and retain
a useful gap when the role cannot be corrected.
Edit only `tools/system_controller.py`. The check runs without provider calls.
