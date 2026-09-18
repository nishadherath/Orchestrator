import unittest
from wsgi_app.request_state import current_metadata, run_request


class StateTests(unittest.TestCase):
    def test_metadata_is_visible_during_request(self):
        self.assertEqual(run_request({"id": 1}, current_metadata), {"id": 1})


if __name__ == "__main__": unittest.main()
