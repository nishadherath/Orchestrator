# Incident: p99 latency on the large tenants

Since last month's changes, p99 response latency has worsened badly for our
largest tenants and is roughly unchanged for the small ones. Catalogue,
checkout and search are all implicated. Gateway, inventory and notifications
look fine. Auth has always been one of the slower services and support have
complained about it for a year, incident or not.

Error rates are unchanged and there is no single spike anywhere, just slower
tails, and only on the big accounts.

You have all seven services and `CHANGELOG.md` for what changed in each last
month. `bench.py [n]` builds n synthetic records and times one request
against every service; n defaults to 400 and any size may be passed.

Produce a ranked list of likely causes with the evidence behind each, and
name the file and function that contain the defect.
