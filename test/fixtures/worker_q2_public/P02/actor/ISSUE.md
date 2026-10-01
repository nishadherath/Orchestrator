# URL-safe timed token regression

Some signed URL tokens containing large repetitive JSON payloads now fail to
load immediately after creation. A separate clock-skew reproducer shows a
future-dated token is accepted even when a maximum age was requested. Repair
both behaviours without changing the token format, weakening signature or
expiry checks, or breaking ordinary small payloads.

The local smoke check is `python3 -B public_check.py`. The fix may edit
`itsdangerous/url_safe.py` and `itsdangerous/timed.py`; do not change the smoke
check, issue, acceptance file or licence. The evaluation includes malformed,
expired and tampered tokens.
