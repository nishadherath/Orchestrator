"""Shared gateway entry point for tenant bearer tokens."""

import jwt

from tenant_keys import TENANT_KEYS


AUDIENCE = "gateway-api"


def verify_request(token: str, expected_tenant: str) -> dict:
    """Return verified claims for the tenant selected by the request route."""
    kid = jwt.get_unverified_header(token)["kid"]
    key = TENANT_KEYS[expected_tenant][kid]
    claims = jwt.decode(token, key, algorithms=["HS256"], audience=AUDIENCE)
    if claims.get("tenant") != expected_tenant:
        raise jwt.InvalidTokenError("tenant does not match route")
    return claims
