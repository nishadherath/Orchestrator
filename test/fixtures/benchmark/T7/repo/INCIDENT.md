# Incident: p99 latency roughly doubled across services

Since last month's changes, p99 response latency has roughly doubled for
catalogue and checkout. Gateway looks unaffected. Auth has always run a bit
slower than the others, incident or not.

There is no single obvious spike anywhere and no change in error rates,
just slower tails on some services and not others. Investigate `gateway`,
`auth`, `catalogue`, and `checkout` (see CHANGELOG.md for what changed last
month in each). You have all four services' code and can reproduce current
timings yourself with `bench.py [n]`, at whatever sizes you find useful.

Produce a ranked list of likely causes with the evidence behind each.
