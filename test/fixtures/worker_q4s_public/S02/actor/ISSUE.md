# Hookspec argument defaults

A hookspec should be allowed to introduce a trailing argument with a default
without breaking a registered implementation that accepts the new argument.
The hookspec metadata in `pluggy/_hooks.py`, plugin validation in
`pluggy/_manager.py` and call dispatch in `pluggy/_callers.py` must agree on
which arguments are required and which value reaches an implementation.
Explicit call values must override spec defaults. Direct, historic and
extra-implementation calls must honour the same contract.

Run `python3 -B public_check.py`. Source edits are limited to
`pluggy/_hooks.py`, `pluggy/_manager.py`, `pluggy/_callers.py`.
Do not edit the issue, public check, acceptance contract or licence.
