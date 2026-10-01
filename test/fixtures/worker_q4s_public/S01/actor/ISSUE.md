# Generator attribute hooks

`attrs.define` and `attrs.field` should accept a generator `on_setattr` hook.
The hook yields the value to assign exactly once, then resumes after the
assignment. Class generation in `attr/_make.py`, callable inspection in
`attr/_compat.py`, the public `attr/_next_gen.py` API and `attr/setters.py`
must preserve the invariant that ordinary hooks still transform values once,
while a generator sees the assigned value when it resumes. A hook yielding
twice must fail rather than silently discard work.

Run `python3 -B public_check.py`. Source edits are limited to
`attr/_compat.py`, `attr/_make.py`, `attr/_next_gen.py`, `attr/setters.py`.
Do not edit the issue, public check, acceptance contract or licence.
