# Retry waits fail only after the first attempt

Some callers supply a falsy wait value to request immediate retry. Others
compose a plain callable with a wait strategy. Both patterns fail when a
retry actually occurs; asynchronous callers show the same falsy-wait problem.
Restore those behaviours without changing ordinary wait strategies or making
invalid numeric combinations silently valid.

Run `python3 -B public_check.py`. Edit only `tenacity/__init__.py`,
`tenacity/asyncio/__init__.py` and `tenacity/wait.py`. The evaluation checks
sync and async retry paths and composition beyond the smoke check.
