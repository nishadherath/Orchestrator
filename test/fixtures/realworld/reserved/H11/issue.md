# Preserve cost and resume state through transient tool failures

`run` receives deterministic tool events containing `status` and `cost_usd`.
Charge every event, retry one timeout or rate limit when budget permits, and
return an honest incomplete state for partial output or exhaustion. Change only
`runner/recovery.py`.
