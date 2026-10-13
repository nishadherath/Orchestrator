# Optional paid meaning tier

The supplied scripts do not run paid passes, provision credentials or change
providers. Deep work is a separate decision. Honour standing operator
authorisation for Graft-selected source transfers within its actual scope;
do not ask for the same authorisation again or extend it to unrelated API use.
Without such authority, establish the intended provider/source scope before
executing a deep pass. Give an estimate of incremental API cost and duration.

Read current `graft build --help` and provider documentation. Load credentials
through the project's approved mechanism without printing them, placing them
on a command line or embedding them in this skill. Keep provider/model/base URL
in local configuration and keep source scope explicit on every paid build.

Concept reads, forced-tool synthesis and per-symbol replies need different
validation. A successful plain completion does not prove that a forced tool
call will return valid arguments within the configured output budget. Inspect
the actual response class: transport/authentication, rate limit, empty reply,
truncated output, invalid tool arguments or mismatched symbol IDs.

Use a small, authorised provider-specific probe before a large pass. If evidence
supports a transient transport/rate-limit failure, one bounded cached retry may
be reasonable. Stop an unchanged retry after repeated empty/unparseable replies;
diagnose request shaping or parser compatibility. Do not assume a model family
always behaves the same way or silently switch to another paid provider.

The original Orchestrator had a DeepSeek compatibility adapter for reasoning,
output limits and symbol IDs, and an unresolved forced-tool summary failure.
That adapter is not redistributed as a universal repair. This package does not
claim to fix that failure. Retain partial evidence and old caches rather than
calling a degraded meaning tier complete.

After any paid pass, verify concept coverage and symbol-summary states, then
retrieve a representative concept and actual source. Report observed usage,
pricing date/source, cached versus uncached assumptions, unresolved costs and
failures. Unknown usage is not zero. `--allow-partial` accepts a degraded tier;
use it only when that tradeoff matches the operator's intended result.
