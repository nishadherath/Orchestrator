"""Shared gateway entry point for tenant bearer tokens."""

import jwt

from tenant_keys import TENANT_KEYS


AUDIENCE = "gateway-api"


def verify_request(token: str, expected_tenant: str) -> dict:
    """Return verified claims for the tenant selected by the request route."""
    if expected_tenant not in TENANT_KEYS:
        raise jwt.InvalidTokenError("unknown route tenant")
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    if kid not in TENANT_KEYS[expected_tenant]:
        raise jwt.InvalidTokenError("unknown signing key for route tenant")
    claims = jwt.decode(
        token, TENANT_KEYS[expected_tenant][kid], algorithms=["HS256"],
        audience=AUDIENCE,
        issuer=f"https://id.example/{expected_tenant}",
    )
    if claims.get("tenant") != expected_tenant:
        raise jwt.InvalidTokenError("tenant does not match route")
    return claims
