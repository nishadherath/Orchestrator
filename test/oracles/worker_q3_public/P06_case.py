"""Offline hidden probes for parsed JWKS caching and malformed members."""
import base64
import json
import sys

from jwt import PyJWKSet
from jwt.exceptions import PyJWKClientError
from jwt.jwk_set_cache import JWKSetCache
from jwt.jwks_client import PyJWKClient


def key(name):
    return {"kty": "oct", "k": base64.urlsafe_b64encode((name + "-secret").encode()).rstrip(b"=").decode(), "kid": name, "alg": "HS256"}


def run(row):
    kind = row["kind"]
    try:
        if kind == "parsed-hit":
            client = PyJWKClient("https://invalid.test/jwks")
            parsed = PyJWKSet.from_dict({"keys": [key("one")]})
            client.jwk_set_cache.put(parsed)
            return client.get_jwk_set() is parsed
        if kind == "normalise":
            cache = JWKSetCache(300)
            cache.put({"keys": [key("one")]})
            return isinstance(cache.get(), PyJWKSet)
        if kind == "identity":
            client = PyJWKClient("https://invalid.test/jwks")
            client.jwk_set_cache.put({"keys": [key("one")]})
            first = client.get_jwk_set()
            return first is client.get_jwk_set()
        if kind == "transformed":
            class Filtered(PyJWKClient):
                def fetch_data(self):
                    self.jwk_set_cache.put({"keys": [key("one"), key("two")]})
                    return {"keys": [key("one")]}

            client = Filtered("https://invalid.test/jwks")
            first = client.get_jwk_set()
            second = client.get_jwk_set()
            return [[item.key_id for item in first.keys], [item.key_id for item in second.keys], first is second]
        if kind == "malformed-member":
            parsed = PyJWKSet.from_dict({"keys": [None, key("one")]})
            return [item.key_id for item in parsed.keys]
        if kind == "bad-component":
            parsed = PyJWKSet.from_dict({"keys": [{"kty": "oct", "k": 9}, key("one")]})
            return [item.key_id for item in parsed.keys]
        if kind == "clear":
            cache = JWKSetCache(300)
            cache.put({"keys": [key("one")]})
            cache.put(None)
            return cache.get() is None
        if kind == "bad-response":
            class Invalid(PyJWKClient):
                def fetch_data(self):
                    return [key("one")]

            Invalid("https://invalid.test/jwks").get_jwk_set()
            return "accepted-invalid"
    except Exception as exc:
        return type(exc).__name__
    raise ValueError(kind)


print(json.dumps(run(json.loads(sys.stdin.read())), sort_keys=True))
