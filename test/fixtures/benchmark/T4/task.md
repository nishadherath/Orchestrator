`store.py` defines `KVStore`, the old storage interface. Port every one of
its six callers (`cache.py`, `sessions.py`, `counters.py`, `settings.py`,
`flags.py`, `history.py`) to a new interface, `Store`, and remove `KVStore`
entirely once nothing uses it. Do not change `test_callers.py` or
`test_new_interface.py`.

`Store`'s contract:

- `write(key, value)`: stores a value, same as `KVStore.set`.
- `read(key)`: returns the stored value, or `None` if the key is missing
  (unlike `KVStore.get`, which raised `KeyError`).
- `remove(key)`: deletes a key if present; does nothing if the key is
  missing (unlike `KVStore.delete`, which raised `KeyError`).
- `keys()`: returns the stored keys, sorted, same as `KVStore.list_keys`.

Update each caller to use `Store`'s methods instead of `KVStore`'s, and
adjust its logic where the two interfaces disagree (a `try`/`except
KeyError` around a `get` or `delete` call becomes a plain `None` check or a
plain call, since `read` and `remove` never raise for a missing key). Every
caller's own external behaviour must stay exactly as it is now: this is a
port, not a change in what any of the six modules does.

When you are done, run this yourself and confirm it passes before
reporting back:

    python3 -m unittest discover -s . -p "test_*.py"
