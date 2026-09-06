"""Behaviour tests for the six caller modules. Do not edit; see task.md.

These pass against the starting state already: they are what "existing
suite green throughout" means. They must still pass after the port, since
the port is only supposed to change which storage interface is used
underneath, not what any caller does from the outside.
"""
import unittest

import cache
import counters
import flags
import history
import sessions
import settings


class TestCache(unittest.TestCase):
    def test_computes_once_then_remembers(self):
        calls = []

        def compute():
            calls.append(1)
            return "computed-value"

        first = cache.get_or_compute("k1", compute)
        second = cache.get_or_compute("k1", compute)
        self.assertEqual(first, "computed-value")
        self.assertEqual(second, "computed-value")
        self.assertEqual(len(calls), 1)

    def test_invalidate_missing_key_is_safe(self):
        cache.invalidate("never-set")


class TestSessions(unittest.TestCase):
    def test_create_get_end(self):
        sessions.create_session("s1", "alice")
        self.assertEqual(sessions.get_session("s1"), "alice")
        sessions.end_session("s1")
        self.assertIsNone(sessions.get_session("s1"))

    def test_get_missing_session_is_none(self):
        self.assertIsNone(sessions.get_session("never-created"))

    def test_end_missing_session_is_safe(self):
        sessions.end_session("never-created")


class TestCounters(unittest.TestCase):
    def test_increment_from_zero(self):
        self.assertEqual(counters.increment("hits"), 1)
        self.assertEqual(counters.increment("hits"), 2)
        self.assertEqual(counters.increment("hits"), 3)

    def test_reset(self):
        counters.increment("resettable")
        counters.reset("resettable")
        self.assertEqual(counters.increment("resettable"), 1)

    def test_reset_missing_is_safe(self):
        counters.reset("never-incremented")


class TestSettings(unittest.TestCase):
    def test_default_when_unset(self):
        self.assertEqual(settings.get_setting("theme", "light"), "light")

    def test_set_then_get(self):
        settings.set_setting("theme", "dark")
        self.assertEqual(settings.get_setting("theme", "light"), "dark")


class TestFlags(unittest.TestCase):
    def test_disabled_by_default(self):
        self.assertFalse(flags.is_enabled("beta"))

    def test_enable_then_disable(self):
        flags.enable("beta")
        self.assertTrue(flags.is_enabled("beta"))
        flags.disable("beta")
        self.assertFalse(flags.is_enabled("beta"))

    def test_disable_missing_is_safe(self):
        flags.disable("never-enabled")


class TestHistory(unittest.TestCase):
    def test_record_and_replay_in_order(self):
        history.record("first")
        history.record("second")
        history.record("third")
        self.assertEqual(history.all_events(), ["first", "second", "third"])


if __name__ == "__main__":
    unittest.main()
