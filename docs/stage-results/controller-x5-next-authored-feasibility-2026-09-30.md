# X5 next authored development case feasibility

Date: 2026-09-30 Australia/Sydney. Status: **provider-free candidate
selection; no frozen new actor, paid call or Controller pair**. B0 remains the
shipping default and X6 remains sealed.

## Pinned urllib3 proxy redirect candidate: rejected

The [urllib3 advisory](https://github.com/urllib3/urllib3/security/advisories/GHSA-qccp-gfcp-xxvc)
reports a low-level proxy redirect path that forwarded sensitive headers
across origins before its patch. The repository already holds a separately
pinned urllib3 source copy under `test/fixtures/worker_q3_public/P04/actor`
with source commit `f4e4bc31f40f8c94c6a1f1685df28f97ff48c305` and a
fixture version string `0+q3`. This copy is for an unrelated zero-port task;
its version string is not an upstream release identifier.

The [local proxy probe](../../test/results/2026-09-30-controller-x5-urllib3-proxy-feasibility.py)
used that unchanged copy with a loopback HTTP proxy and two synthetic origins.
It called both `ProxyManager.connection_from_url().urlopen` with
`assert_same_host=False` and `ProxyManager.request`. Both calls reached the
redirected origin with `Authorization`, `Cookie` and `Proxy-Authorization`
absent while retaining an ordinary correlation header. The same result was
observed with Windows and WSL Python. The
[saved WSL observation](../../test/results/2026-09-30-controller-x5-urllib3-proxy-feasibility.json)
contains the request-level header booleans and 200 responses. This source
copy has no vulnerable baseline for the proposed task. Do not derive an X5
actor by injecting the advisory's old defect into it. No external network
request or provider call occurred in the probe.

## pytest-asyncio fixture candidate: reproducible, held

The distinct [pytest-asyncio issue #1501](https://github.com/pytest-dev/pytest-asyncio/issues/1501)
concerns order-dependent teardown of managed async fixtures consumed by a
sync test when a loop-factory hook is present. The previous
[E01 qualification](controller-x5-external-e01-preflight-2026-09-30.md)
pinned the v1.4.0 source and pytest 9.1.1, reproduced the failure on Windows
and WSL, and demonstrated that a proposed repair passes an independent
two-factory coverage condition while a narrow control does not. The
[public PR #1553](https://github.com/pytest-dev/pytest-asyncio/pull/1553)
publishes a detailed fix; this issue cannot be called a blind natural case.

A fresh provider-free run on the existing pinned source and local WSL package
cache used the existing E01 reproduction files. It again returned one pass
and one setup error: `test_sync` could not obtain `parent` because pytest had
already torn it down. The run was local and made no model call. This confirms
the symptom remains reproducible in the current host, not that an authored
X5 actor or Controller headroom is qualified.

Before any authored paid producer, copy the source and test dependencies into
a self-contained licensed actor, retain provenance and source hashes, remove
the published fix hint from the *authored* worker report while labelling the
adaptation honestly, and freeze public and protected behaviour before a model
call. A second, independently designed complete repair is still missing.
The public follow-up and protected oracle must check distinct loop factories,
fixture setup and teardown for sync and async consumers in both orders. A
single-factory shortcut and any repair that merely hides a failing test must
fail calibration. The first producer's stop rule must depend on frozen public
evidence only. No S/A eligibility or uplift is inferred from this preflight.

**Inference:** this lifecycle task has more interacting mechanisms than the
short authored regressions that B0 repeatedly solved on its first attempt.
**Untested risks:** a worker may recall the public PR, the proposed repair may
not satisfy all compatibility cases, and a bounded Controller may add no
useful diagnosis. The temporary dependency cache is not a sealed actor or
durable runtime package.
