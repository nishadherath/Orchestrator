# Site-directory queries create paths they do not return

With `ensure_exists=True`, a request for one site path can create every
candidate in the platform's list. This causes unwanted side effects and may
fail where an unreturned directory is not writable. A returned single path
should be the only path created; multipath results should create their returned
members; lazy iterators should create entries only as they are yielded.
Preserve path selection on Unix, XDG and macOS.

Run `python3 -B public_check.py`. Edit only `platformdirs/_xdg.py`,
`platformdirs/api.py`, `platformdirs/macos.py` and `platformdirs/unix.py`.
The checks intercept directory creation, so no system path is changed.
