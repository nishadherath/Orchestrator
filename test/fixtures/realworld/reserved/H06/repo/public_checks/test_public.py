import unittest
from webhooks.dispatcher import process


class WebhookTests(unittest.TestCase):
    def test_one_delivery(self):
        calls = []
        process([{"id":"a","sequence":1,"payload":3}], {}, lambda *x: calls.append(x))
        self.assertEqual(calls, [("a", 3)])


if __name__ == "__main__": unittest.main()
