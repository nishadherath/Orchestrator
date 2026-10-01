"""Shared gateway entry point for tenant bearer tokens."""

import jwt

from tenant_keys import TENANT_KEYS


AUDIENCE = "gateway-api"


def verify_request(token: str, expected_tenant: str) -> dict:
    """Return verified claims for the tenant selected by the request route."""
    keys = TENANT_KEYS.get(expected_tenant)
    if keys is None:
        raise jwt.InvalidTokenError("unknown route tenant")
    kid = jwt.get_unverified_header(token).get("kid")
    key = keys.get(kid)
    if key is None:
        raise jwt.InvalidTokenError("unknown signing key for route tenant")
    claims = jwt.decode(token, key, algorithms=["HS256"], audience=AUDIENCE,
                        issuer=f"https://id.example/{expected_tenant}")
    if claims.get("tenant") != expected_tenant:
        raise jwt.InvalidTokenError("tenant does not match route")
    return claims
