import unittest
from wsgi_app.conditional import respond


class ConditionalTests(unittest.TestCase):
    def test_unconditional_response(self):
        self.assertEqual(respond(b"new", '"v2"')[0], 200)


if __name__ == "__main__": unittest.main()
