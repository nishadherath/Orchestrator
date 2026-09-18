import os, sys, threading, unittest
sys.path.insert(0, os.environ["REALWORLD_ACTOR_ROOT"])
from wsgi_app.request_state import current_metadata, run_request


class HiddenStateTests(unittest.TestCase):
    def test_overlapping_requests_are_isolated(self):
        barrier = threading.Barrier(2)
        seen = []
        errors = []
        def request(identifier):
            try:
                seen.append(run_request({"id": identifier}, lambda: (barrier.wait(1), current_metadata())[1]))
            except Exception as exc: errors.append(exc)
        threads = [threading.Thread(target=request, args=(value,)) for value in ("a", "b")]
        for thread in threads: thread.start()
        for thread in threads: thread.join(2)
        self.assertFalse(errors)
        self.assertEqual({item["id"] for item in seen}, {"a", "b"})
        self.assertIsNone(current_metadata())

    def test_exception_cleans_context(self):
        with self.assertRaises(RuntimeError):
            run_request({"secret": 1}, lambda: (_ for _ in ()).throw(RuntimeError()))
        self.assertIsNone(current_metadata())


if __name__ == "__main__": unittest.main()
