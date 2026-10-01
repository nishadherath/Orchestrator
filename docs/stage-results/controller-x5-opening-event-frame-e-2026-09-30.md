# X5 opening-event frame E screen

Date: 2026-09-30 Australia/Sydney. Status: **provider-free development frame
closed**. B0 remains the shipping default and X6 remains sealed. No paid
producer, Controller or worker call was made.

The [protocol](controller-x5-opening-event-frame-e-protocol-2026-09-30.md)
froze a sixteen-repository, first-event-page cohort and a hash-selected prefix
before screening. A structure-only feed probe established that opening event
payloads contain an issue body. The first collector attempt stopped before
writing output because the feed had 18 adjacent timestamp inversions in
Werkzeug's first page. The protocol was amended to a fixed first-page cohort
before inspecting issue content. This is not an exhaustive time window or a
population estimate; delayed events and later pages may contain omitted
openings.

The [frame](../../test/results/2026-09-30-controller-x5-opening-frame-e.json)
contains four opening events across the fixed cohort. The [exact opening
bodies](../../test/results/2026-09-30-controller-x5-opening-frame-e-selected-bodies.json)
were saved in hash order. Frame SHA-256:
`d14358ae7e834d2a0c130f6516ef8df3e445db51121f9f5b5ea2b72bad16398e`.
Body file SHA-256:
`1bb8f63f6458b1939f9e5ab725fd4b2795d267101a7061967ddb42855a88a52b`.
Explicit UTF-8 verification confirmed URL order, title and body digests,
and selection order for all four rows. A diagnostic verifier using Windows'
default text encoding had initially misread one Unicode arrow; it did not
alter the frozen files.

The [screen record](../../test/results/2026-09-30-controller-x5-opening-frame-e-screen.json)
rejects all four for blind paid work. Werkzeug #3312 names the exact IPv6
parsing fault and a fix. Werkzeug #3313 is an author-closed compatibility
discussion, not a settled failure. Pydantic Settings #993 offers a full
reproduction, likely parser layer and exact regression, but no separate
consequential follow-up gap; source reproduction and an independent oracle
were not attempted. APScheduler #1144 supplies the UTC repair and reports
that its tests pass with it. Neither an opening event nor recency alone keeps
the diagnosis out of natural issue text.

This frame yields **zero** qualified paid cases and no matched S/A comparison.
It does not show that natural tasks cannot provide Controller headroom. The
next intake would need a substantially larger fixed cohort of initial
reports or an independent private task source, with acceptance qualification
before spend. Repeating the same four reports, redacting their diagnosis or
changing their selection order would bias the comparison. No Controller
uplift is measured.
