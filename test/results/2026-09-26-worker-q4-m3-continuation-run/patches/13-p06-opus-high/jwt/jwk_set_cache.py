import time
from typing import Optional, Union

from .api_jwk import PyJWKSet, PyJWTSetWithTimestamp
from .exceptions import PyJWKSetError
from .types import JWKDict


class JWKSetCache:
    def __init__(self, lifespan: float) -> None:
        self.jwk_set_with_timestamp: Optional[PyJWTSetWithTimestamp] = None
        self.lifespan = lifespan

    def put(self, jwk_set: Union[PyJWKSet, JWKDict, None]) -> None:
        """Store a JWK Set in the cache.

        Accepts either an already-parsed :class:`PyJWKSet` or the raw JSON
        object returned by a JWKS endpoint; raw data is parsed once, here, so
        that reads never have to reparse it. Passing ``None`` clears the
        cache; any other value is an invalid JWK Set and is rejected.

        :raises PyJWKSetError: If *jwk_set* is neither ``None``, a
            ``PyJWKSet``, nor a JSON object.
        """
        if jwk_set is None:
            # clear cache
            self.jwk_set_with_timestamp = None
            return

        if isinstance(jwk_set, PyJWKSet):
            parsed = jwk_set
        elif isinstance(jwk_set, dict):
            parsed = PyJWKSet.from_dict(jwk_set)
        else:
            raise PyJWKSetError("Invalid JWK Set value")

        self.jwk_set_with_timestamp = PyJWTSetWithTimestamp(parsed)

    def get(self) -> Optional[PyJWKSet]:
        if self.jwk_set_with_timestamp is None or self.is_expired():
            return None

        return self.jwk_set_with_timestamp.get_jwk_set()

    def is_expired(self) -> bool:
        return (
            self.jwk_set_with_timestamp is not None
            and self.lifespan > -1
            and time.monotonic()
            > self.jwk_set_with_timestamp.get_timestamp() + self.lifespan
        )
