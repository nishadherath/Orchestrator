# Specific exception for invalid joiner context

An invalid zero-width joiner or non-joiner context in an IDNA label should
raise `InvalidCodepointContext`, not a generic `IDNAError`. Truly unknown
adjacent Unicode data should still raise `IDNAError`. The requested change
is confined to `idna/core.py`; `idna/codec.py` is available only if a narrow
supporting edit is needed. There is no cross-component contract in this task.

Run `python3 -B public_check.py`. Source edits are limited to
`idna/core.py` and `idna/codec.py`.
Do not edit the issue, public check, acceptance contract or licence.
