# X5 H02b B0 producer spend notice, 2026-09-30

The [H02 first root](controller-x5-h02-first-attempt-stop-2026-09-30.md)
stopped before a provider process began and its USD 5 reservation settled at
zero. H02b is a new root and manifest after the bounded Graft graph fix; it
does not replay the stopped invocation. The new [manifest](../../test/results/2026-09-30-controller-x5-h02b-producer-manifest.json)
has SHA-256 `75eb7fe26ce4ee5d9cb123181317a85cb549006c881b79d9f4bdad88d04f317b`.
Its [dated approval record](../../test/results/2026-09-30-controller-x5-h02b-producer-notice.json)
binds the operator's approval of planned tests to one B0 Sonnet-low Q4U
attempt, then a provider-free H02 grade. The root hard cap is **USD 5**
API-equivalent. This manifest authorises no S/A calls.

The projection remains **USD 0.2 to 2.0** API-equivalent. Assumptions are
10,000 to 100,000 ordinary input tokens, 20,000 to 100,000 five-minute cache
write tokens, 100,000 to 1,000,000 cache read tokens and 5,000 to 50,000
output tokens. At the 2026-09-30 [Claude Sonnet 5 rates](https://platform.claude.com/docs/en/models/sonnet-5/overview)
of USD 2, 2.50, 0.20 and 10 per million respectively, those endpoints yield
about USD 0.14 to 1.15. The wider projection allows extra tool turns and
uncertain cache use. The Claude.ai subscription receipt reports API-equivalent
cost rather than a separate API invoice. The manifest stops on uncertainty,
budget breach or drift. Only the public acceptance state can make a later
S/A comparison eligible under a separate manifest.
