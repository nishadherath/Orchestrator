import os, sys, unittest
sys.path.insert(0, os.environ["REALWORLD_ACTOR_ROOT"])
from wsgi_app.conditional import respond


class HiddenConditionalTests(unittest.TestCase):
    def test_matching_validator(self):
        status, body, headers = respond(b"fresh", '"v2"', '"v2"')
        self.assertEqual((status, body), (304, b""))
        self.assertEqual(headers, {"ETag": '"v2"', "Content-Length": "0"})

    def test_stale_validator_gets_fresh_representation(self):
        status, body, headers = respond(b"fresh", '"v2"', '"v1"')
        self.assertEqual((status, body), (200, b"fresh"))
        self.assertEqual(headers["ETag"], '"v2"')
        self.assertEqual(headers["Content-Length"], "5")


if __name__ == "__main__": unittest.main()
