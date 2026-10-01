# X5 opening-event frame E: prospective development intake

Frozen at 2026-09-30 03:39:27 UTC, before reading any issue body in this
frame. A structure-only request to `pallets/werkzeug` returned 98 repository
events, seven opening events, and an opening payload with a body field; it
did not print titles or bodies. This is an adaptive development search after
frames B-D found no blind paid case. It is not a reserved sample or a
population estimate. B0 remains the shipping default and X6 remains sealed.

## Fixed collection

Read public repository events from these sixteen repositories in this order:
`pallets/werkzeug`, `pallets/jinja`, `pallets/flask`,
`pallets/itsdangerous`, `pytest-dev/pluggy`, `python-attrs/attrs`,
`python-trio/trio`, `encode/httpx`, `encode/httpcore`,
`agronholm/apscheduler`, `aio-libs/yarl`, `pydantic/pydantic-settings`,
`Textualize/rich`, `pypa/packaging`, `python-poetry/cleo`, and
`psf/requests`. Request exactly the first `per_page=100` event page for each
repository, with no page replacement. Include opening events timestamped on
or after 2026-09-26 00:00:00 UTC. This fixed API-page cohort is not an
exhaustive time window: busy repositories may have additional qualifying
events on later pages, and the API can deliver events late. Record each
page's minimum and maximum event times. GitHub documents a 300-event,
30-day timeline limit and possible event latency. A delayed or missing
opening event cannot be inferred from a current issue listing.

The first attempt, before any frame was written or issue content was
inspected, stopped on a false ordering assumption: the first Werkzeug page
had 18 adjacent timestamp inversions. The rule was amended from a presumed
complete cutoff window to this fixed first-page cohort before collection.

Include only `IssuesEvent` with `payload.action == "opened"`, an issue rather
than a pull request, and an event timestamp at or after the cutoff. Record
event ID, repository, issue URL and number, opening title, event and issue
creation times, body-null marker and SHA-256 of the UTF-8 decoded opening
body string. Hash an empty string for null. Save request/final URLs, HTTP
status, server date, page counts and per-repository event/issue counts. Reject
duplicate event IDs or issue URLs and malformed event payloads.

Sort included issues by SHA-256 of the UTF-8 string
`x5-frame-e-2026-09-30-033927Z\n` plus the canonical issue URL. Screen the
first 30, or all if fewer. Save their exact opening titles and body strings
separately, and verify their hashes before judging. Previously screened URLs
stay in the denominator and are marked as overlaps; they are not replaced.
No repository, cutoff, order, or sample size changes after collection.

## Admission and stopping

An opening body can still disclose the answer. Reject a blind repair when the
opening report or actor source names the fault path or fix, when the worker
runtime cannot reproduce it deterministically, or when the correct behaviour
is an unsettled policy choice. Later comments and PRs may identify
contamination and affect rejection, but their diagnosis must not be removed
from an otherwise natural issue to manufacture a task. The opening event is
an archived public input, not a claim that a current public page remains
blind or that model memory is absent.

A symptom-only lead remains provider-free research until its source revision,
license and dependencies are pinned; its opening symptom reproduces in the
worker host; and an independent public follow-up plus protected oracle are
qualified against baseline, a plausible narrow wrong repair and two complete
repairs. Freeze the target population, paired analysis, arm order, cost caps
and a dated manifest-bound notice before any producer call. Close a producer
that resolves the public risk before S/A review. A single development pair
cannot open X6 or promote Controller routing.
