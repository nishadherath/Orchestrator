# X5 K01 development comparison: tenant-bound signing key review

Date: 2026-09-30 Australia/Sydney. Status: frozen, provider-free design.
No K01 provider call or Controller quality gain is claimed here. B0 remains the
shipping default and X6 remains sealed.

## Prospective case and selection

K01 is an authored gateway regression on the pinned PyJWT checkout
`1d41a6478e1562e68ff667fcd703356acf085f68` (MIT). The public issue is
Blue tenant's scheduled key rotation. The public check covers old and new
Blue keys, Red traffic, a plain route mismatch, audience and expiry. It does
not test two tenants reusing one key ID or an issuer substituted under a
different route. The uneditable `key_feed.json` lists `shared` for both Red
and Blue; its exact quote and SHA-256 are in K01's risk record. This is a
consequential, public-observable verification gap. The predeclared next check
is to exercise both keys and reject cross-tenant issuer or route confusion.

The two negative control packets are C01, a tenant-scoped verifier with a
single known missing mapping and strong public trust checks, and M01, an
issuer retirement request with no issuer identity or overlap policy. Both are
ineligible under the same rule. These controls test rubric specificity
provider-free; they are not worker outcome controls and cannot establish a
false-review rate in production.

The [frozen catalogue](../../test/fixtures/controller_x5_public_risk/catalogue-k01.json)
binds actor bytes, risk, controls, editable paths, variants, pinned upstream
commit and the isolated oracle. The actor contains only public material.
Baseline fails the new-key public check; a narrow mapping fix passes public
but fails protected trust cases; two independent complete repairs pass both.
The fixture test is in
`test/harness/controller_x5_public_risk_fixture_tests.py`.

## Single-use pilot contract

One ordinary B0 Sonnet-low producer is admitted. A settled, terminal,
writer-stopped and identity-valid public success with the frozen public risk
is the only continuation trigger. The checkpoint clones identical accepted
public bytes into S and A. Each gets the original issue, public check, risk
finding, discriminating check and identical producer edit summary. S gets one
Sonnet-low review call. A first gets one bounded source-cited Controller
investigation and then the same Sonnet-low review policy. No hidden oracle is
read until both reviews have settled. Public failure or any uncertain receipt
stops the run without replay.

The manifest-bound ceiling is USD 5 per root, USD 0.5 for the public
assessment, one Controller invocation capped by its runtime at USD 4, and
USD 20 overall. The expected reported API-equivalent spend is about
USD 0.2–6, with actual subscription billing uncertain. The operator's
2026-09-30 approval covers planned tests; the runner still requires an exact
dated notice bound to the manifest before each paid mode. Producer spend is
counted once. Results separate protected quality, critical errors, false
completion claims, elapsed time and reconciled cost. A positive single K01
result is provisional and cannot promote routing. X0-style power planning,
fresh reserved cases and independent review remain necessary.

## Stop and validity rules

The run stops on source or manifest drift, an active writer, identity failure,
open charge, missing public evidence, bad risk citation, unexplained Controller
handoff, failed public check, or any prior use of a root. After the matched
pair, a producer already at full protected quality or no measured A over S
gain closes this development candidate. The public control packets do not
justify selective paid retries. Earlier R01/R02/P02/F01–F03 outcomes are
historical and are never replayed or used to select K01.
