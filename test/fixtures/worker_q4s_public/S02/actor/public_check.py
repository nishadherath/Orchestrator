"""Public smoke test for hookspec defaults."""
import unittest

import pluggy


class DefaultsTest(unittest.TestCase):
    def test_spec_default_and_override(self):
        spec = pluggy.HookspecMarker("q4s")
        impl = pluggy.HookimplMarker("q4s")

        class Api:
            @spec
            def collect(self, item, label="default"):
                pass

        class Plugin:
            @impl
            def collect(self, item, label):
                return item, label

        manager = pluggy.PluginManager("q4s")
        manager.add_hookspecs(Api)
        manager.register(Plugin())
        self.assertEqual(manager.hook.collect(item=2), [(2, "default")])
        self.assertEqual(manager.hook.collect(item=2, label="call"), [(2, "call")])


if __name__ == "__main__":
    unittest.main()
