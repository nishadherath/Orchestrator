# Keep rollout decisions current and tenant-specific

The local rollout service accepts tenant defaults, user overrides and an
emergency kill switch. Operators saw a changed default leave an old decision
in place, and two tenants with the same flag and user name receive the same
decision despite different policies. An emergency kill also failed to stop a
user whose override had previously enabled the flag. The trace records one
reproduction.

Decisions must follow current policy for the given tenant. The kill switch
overrides other settings; otherwise a user override wins over a tenant
default, and an unset flag is disabled. A policy update must take effect on
the next evaluation without leaking another tenant's decision. Change only
`cache.py`, `decision.py` and `report.json`. Keep `policy.py`, `app.py`, the
trace and public check unchanged. Record what you verified and what remains
to be tested.

Run `python3 -B public_check.py` if an execution tool is available.
