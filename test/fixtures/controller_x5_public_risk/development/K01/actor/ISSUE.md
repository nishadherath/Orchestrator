# Blue tenant rejects tokens after a scheduled signing key rotation

The Blue identity service began signing with key ID `blue-2026` while the
gateway still accepts Blue's previous `blue-old` tokens. New Blue requests
now fail at the gateway. Restore overlapping key acceptance for this rotation
without weakening tenant, audience or expiry checks. Red tenant traffic must
continue to work. The key feed and a short incident trace are supplied below.

Run `python3 -B public_check.py` locally. Repair only `auth_gateway.py` and
`tenant_keys.py`. Do not edit the issue, feed, trace, checks or vendored JWT
package. The gateway is a shared endpoint; callers provide the expected
tenant from the authenticated route, not from token contents.
