"""Auth service: issues a session token after checking it against the
revoked-token list."""
import time

_REVOKED_TOKENS = [f"revoked-{i}" for i in range(60000)]


def _is_revoked(token):
    return token in _REVOKED_TOKENS


def handle_request(n=1):
    """n is accepted for a uniform interface with the other services; token
    issuance does not depend on it."""
    token = f"session-{int(time.time() * 1000000)}"
    if _is_revoked(token):
        return "denied"
    return f"token:{token}"
