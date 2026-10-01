"""Public gateway regression checks for the observed rotation."""

import time
import unittest

import jwt

from auth_gateway import verify_request
from tenant_keys import BLUE_2026, BLUE_OLD, RED_SHARED


def token(key, kid, tenant, *, audience="gateway-api", expires_in=3600):
    claims = {"iss": f"https://id.example/{tenant}", "tenant": tenant,
              "aud": audience, "exp": int(time.time()) + expires_in}
    return jwt.encode(claims, key, algorithm="HS256", headers={"kid": kid})


class RotationChecks(unittest.TestCase):
    def test_new_blue_key(self):
        claims = verify_request(token(BLUE_2026, "blue-2026", "blue"), "blue")
        self.assertEqual("blue", claims["tenant"])

    def test_old_blue_key_still_works(self):
        self.assertEqual("blue", verify_request(
            token(BLUE_OLD, "blue-old", "blue"), "blue")["tenant"])

    def test_red_unchanged(self):
        self.assertEqual("red", verify_request(
            token(RED_SHARED, "shared", "red"), "red")["tenant"])

    def test_route_tenant_mismatch_rejected(self):
        with self.assertRaises(Exception):
            verify_request(token(RED_SHARED, "shared", "red"), "blue")

    def test_wrong_audience_rejected(self):
        with self.assertRaises(Exception):
            verify_request(token(BLUE_OLD, "blue-old", "blue",
                                 audience="another-api"), "blue")

    def test_expired_rejected(self):
        with self.assertRaises(Exception):
            verify_request(token(BLUE_OLD, "blue-old", "blue",
                                 expires_in=-60), "blue")


if __name__ == "__main__":
    unittest.main()
