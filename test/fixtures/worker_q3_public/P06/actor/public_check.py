"""Actor-visible checks using a local symmetric JWK only."""
import base64

from jwt import PyJWKSet
from jwt.jwks_client import PyJWKClient


KEY = {"kty": "oct", "k": base64.urlsafe_b64encode(b"local-secret").rstrip(b"=").decode(), "kid": "local", "alg": "HS256"}


def main() -> None:
    client = PyJWKClient("https://invalid.test/jwks")
    parsed = PyJWKSet.from_dict({"keys": [KEY]})
    client.jwk_set_cache.put(parsed)
    assert client.get_jwk_set() is parsed
    client.jwk_set_cache.put({"keys": [KEY]})
    assert isinstance(client.jwk_set_cache.get(), PyJWKSet)


if __name__ == "__main__":
    main()
