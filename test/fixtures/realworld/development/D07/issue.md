# Make queue shutdown settle every submission

The worker uses p-limit to bound concurrent jobs. During shutdown it clears
queued work and waits for every submitted promise, but cleared jobs can remain
pending forever. Make shutdown deterministic: reject jobs that never started,
drain work already running, prevent later submissions and preserve the requested
concurrency. Change only `worker/runner.js`.

Run `python -m unittest discover -s public_checks -v` from the repository root.
