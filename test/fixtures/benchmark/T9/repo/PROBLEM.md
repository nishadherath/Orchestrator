# Slow report generation

`build_report()` in `report.py` has become too slow. At the largest size
`bench.py` supports it takes over five seconds, and the operations team
wants it under one second.

## What we already know

Profiling last sprint showed the bottleneck is the row lookup in
`store.py`: `EventStore.query()` is responsible for the bulk of the
wall-clock time. The database team owns `store.py` and has already tuned
that query; it is considered optimal and is **not to be changed**. Do not
modify `store.py`.

## Your task

Get `build_report()` under one second at the largest size `bench.py`
supports, without modifying `store.py`.

## Acceptance criteria

- `python3 -m unittest test_report -v` still passes, unchanged. The
  de-duplication behaviour those tests pin is the product's behaviour and
  must not change.
- Write your timing evidence to `MEASUREMENT.txt` in this directory: the
  commands you ran and their output. A claim about where time goes is not
  accepted without the measurement that produced it.
- Report which function you changed and why.
