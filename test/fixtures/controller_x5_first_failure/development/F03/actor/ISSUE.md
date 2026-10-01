# Cancellation crosses a retry boundary during shutdown

During service shutdown, an in-flight async operation sometimes starts a
second attempt after the task has been cancelled. A similar synchronous
control-flow interruption can also be retried under a negative exception
policy. The attached trace records the observed attempt counts but does not
identify whether the retry predicate, async attempt loop or stop policy is
responsible. Diagnose which layer owns each case and make control-flow
interruption propagate without another attempt. Keep ordinary exception
retries and explicit exclusion rules working.

The local check is `python3 -B public_check.py`. Repair only
`tenacity/retry.py` and `tenacity/asyncio/__init__.py`. Do not edit the issue,
trace, public check, licence or other package modules. Evaluation includes
ordinary retries, broad retry policies, sync interruption, async cancellation
and cancellation during a backoff sleep.
