import os, sys, unittest
sys.path.insert(0, os.environ["REALWORLD_ACTOR_ROOT"])
from webhooks.dispatcher import process


class Sink:
    def __init__(self): self.effects = {}; self.crash_once = False
    def apply(self, key, payload):
        self.effects.setdefault(key, payload)
        if self.crash_once:
            self.crash_once = False
            raise RuntimeError("crash after effect")


class HiddenWebhookTests(unittest.TestCase):
    def test_duplicates_and_reordering(self):
        state, sink = {}, Sink()
        events = [{"id":"b","sequence":2,"payload":2},{"id":"a","sequence":1,"payload":1},{"id":"a","sequence":1,"payload":1}]
        process(events, state, sink.apply)
        self.assertEqual(list(sink.effects), ["a", "b"])
        self.assertEqual(process(events, state, sink.apply), 0)

    def test_crash_replay_uses_same_idempotency_key(self):
        state, sink = {}, Sink(); sink.crash_once = True
        event = [{"id":"x","sequence":1,"payload":7}]
        with self.assertRaises(RuntimeError): process(event, state, sink.apply)
        self.assertEqual(sink.effects, {"x": 7})
        process(event, state, sink.apply)
        self.assertEqual(sink.effects, {"x": 7})


if __name__ == "__main__": unittest.main()
