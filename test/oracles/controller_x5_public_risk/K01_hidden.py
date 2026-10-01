"""Host-only acceptance. Run with the actor directory on PYTHONPATH."""

import time
import unittest
import io
import json

import jwt

from auth_gateway import verify_request
from tenant_keys import BLUE_2026, BLUE_OLD, BLUE_SHARED, RED_SHARED


def token(key, kid, tenant, *, issuer=None, audience="gateway-api", expires_in=3600):
    claims = {"iss": issuer or f"https://id.example/{tenant}",
              "tenant": tenant, "aud": audience,
              "exp": int(time.time()) + expires_in}
    return jwt.encode(claims, key, algorithm="HS256", headers={"kid": kid})


class ProtectedGatewayChecks(unittest.TestCase):
    def test_rotated_blue(self):
        self.assertEqual("blue", verify_request(token(
            BLUE_2026, "blue-2026", "blue"), "blue")["tenant"])

    def test_previous_blue(self):
        self.assertEqual("blue", verify_request(token(
            BLUE_OLD, "blue-old", "blue"), "blue")["tenant"])

    def test_blue_and_red_reuse_key_id(self):
        self.assertEqual("blue", verify_request(token(
            BLUE_SHARED, "shared", "blue"), "blue")["tenant"])
        self.assertEqual("red", verify_request(token(
            RED_SHARED, "shared", "red"), "red")["tenant"])

    def test_red_signature_cannot_impersonate_blue_route(self):
        forged = token(RED_SHARED, "shared", "blue",
                       issuer="https://id.example/red")
        with self.assertRaises(jwt.InvalidTokenError):
            verify_request(forged, "blue")

    def test_unrecognised_issuer_rejected(self):
        forged = token(BLUE_OLD, "blue-old", "blue",
                       issuer="https://id.example/unrelated")
        with self.assertRaises(jwt.InvalidTokenError):
            verify_request(forged, "blue")

    def test_wrong_audience_rejected(self):
        with self.assertRaises(jwt.InvalidTokenError):
            verify_request(token(BLUE_OLD, "blue-old", "blue",
                                 audience="other-api"), "blue")

    def test_expired_rejected(self):
        with self.assertRaises(jwt.InvalidTokenError):
            verify_request(token(BLUE_OLD, "blue-old", "blue",
                                 expires_in=-60), "blue")

    def test_unknown_key_rejected(self):
        with self.assertRaises(Exception):
            verify_request(token(BLUE_OLD, "unknown", "blue"), "blue")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ProtectedGatewayChecks)
    result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    failed = {test._testMethodName for test, _ in result.failures + result.errors}
    critical = {"test_blue_and_red_reuse_key_id",
                "test_red_signature_cannot_impersonate_blue_route",
                "test_unrecognised_issuer_rejected"}
    cases = [{"name": name, "passed": name not in failed,
              "critical": name in critical, "weight": 2 if name in critical else 1}
             for name in sorted(method for method in dir(ProtectedGatewayChecks)
                                if method.startswith("test_"))]
    print(json.dumps({"cases": cases}, sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() else 1)
