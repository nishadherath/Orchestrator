# X5 historical opening-event frame F screen

Date: 2026-09-30 Australia/Sydney. Status: **provider-free development frame
closed**. B0 remains the shipping default and X6 remains sealed. No worker,
Controller or paid producer was launched.

The [protocol](controller-x5-opening-event-frame-f-protocol-2026-09-30.md)
froze 26 Python repositories, one public event page per repository, a
2026-09-01 opening-event cutoff and hash order before collection. The
[frame](../../test/results/2026-09-30-controller-x5-opening-frame-f.json)
contains 38 opening issues and a fixed 30-row selected prefix. Its SHA-256
is `80885c6fc51e47b02b37251e88e86da18a6cf6a61b7d4913821bc584e84bdb8d`.
The [exact selected bodies](../../test/results/2026-09-30-controller-x5-opening-frame-f-selected-bodies.json)
have SHA-256 `5cef7aed276afafde091ebd4c8dc1baf008d0fcabfed7f0b2526560061616499`.
Explicit UTF-8 verification passed title/body hashes and hash order for
30/30 rows. This is a first-page API cohort, not a complete September issue
window or a population rate estimate.

The [row screen](../../test/results/2026-09-30-controller-x5-opening-frame-f-screen.json)
records 30/30 decisions, seven overlaps with frames C, D or E, and **zero
blind paid admissions**. Most opening bodies already state a cause, fix or
linked PR: aiohttp #13868 identifies case-sensitive header deduplication;
APScheduler #1141 gives a synchronous-callback diagnosis and an async
replacement; SQLAlchemy #13616 states its `TextClause` transformation and
the intended literal semantics; httpcore #1110 traces the pool race and
links a fix. Other rows are deprecation, documentation or policy requests,
spam, or lack qualified database/visual acceptance. This screen does
not claim those underlying reports are unimportant.

Jinja #2274 was the one provider-free preflight. On installed Jinja 3.1.6,
an in-memory template loaded by a normal string succeeded. Loading the same
template by `StrEnum` in a **fresh** environment raised the reported
`SyntaxError` at generated `name = <T.foo: 'template.jinja'>`; loading a
normal string first masked the issue through the template cache. Installed
source shows `CodeGenerator` writes `f"name = {self.name!r}"`. The [maintainer
reply](https://github.com/pallets/jinja/issues/2274) closed the issue as
not planned and said the API expects strings. Thus the symptom is real, but
the requested StrEnum support lacks an accepted repair contract. No Jinja
worker or protected oracle was run.

**Observation:** even the historical opening bodies often contain the exact
diagnosis. **Inference:** merely moving from current issue pages to archived
opening events has not created Controller headroom in these two development
cohorts. **Untested:** a private unresolved task population or a genuinely
symptom-only natural report with deterministic multi-system acceptance may
still support a useful A/S comparison. No Controller quality effect was
measured, and this frame cannot open X6.
