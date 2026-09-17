#!/usr/bin/env python3
"""Offline regression tests for the live Controller adapter."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_module():
    name = "evaluation_live_controller"
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "tools" / "evaluation_live_controller.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class LiveControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.subject = load_module()

    def test_qualification_covers_nested_accounting_without_model_calls(self):
        with tempfile.TemporaryDirectory(prefix="live-controller-qualification-") as folder:
            value = self.subject.run_qualification(Path(folder))
        self.assertEqual(value["result"], "PASS", value)
        self.assertEqual(value["model_calls"], 0)
        self.assertTrue(all(value["checks"].values()))

    def test_validation_rejects_tampering(self):
        source = json.loads(self.subject.DEFAULT_OUTPUT.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(prefix="live-controller-evidence-",
                                         dir=ROOT / "test" / "results") as folder:
            path = Path(folder) / "evidence.json"
            self.subject.atomic_json(path, source)
            self.assertTrue(self.subject.validate(path)[0])
            source["model_calls"] = 1
            self.subject.atomic_json(path, source)
            self.assertFalse(self.subject.validate(path)[0])

    def test_workspace_cannot_be_nested_in_actor(self):
        with tempfile.TemporaryDirectory(prefix="live-controller-boundary-") as folder:
            actor = Path(folder) / "actor"
            actor.mkdir()
            request = self.subject.ControllerRequest(
                actor_root=actor, controller_root=actor / "controllers",
                issue="repair", allowed_edits=("file.py",), observations=(),
                allowance_usd=1.0, invocation_id="inv-001",
            )
            adapter = self.subject.LiveControllerAdapter(
                lambda *args, **kwargs: self.fail("provider boundary should not run"))
            with self.assertRaisesRegex(ValueError, "separate"):
                adapter.run(request)
        self.assertFalse((actor / "controllers").exists())

    def test_duplicate_workspace_refuses_redispatch(self):
        with tempfile.TemporaryDirectory(prefix="live-controller-duplicate-") as folder:
            root = Path(folder)
            actor = root / "actor"
            actor.mkdir()
            controller_root = root / "controllers"
            (controller_root / "inv-001").mkdir(parents=True)
            request = self.subject.ControllerRequest(
                actor_root=actor, controller_root=controller_root,
                issue="repair", allowed_edits=("file.py",), observations=(),
                allowance_usd=1.0, invocation_id="inv-001",
            )
            adapter = self.subject.LiveControllerAdapter(
                lambda *args, **kwargs: self.fail("provider boundary should not run"))
            with self.assertRaisesRegex(ValueError, "already exists"):
                adapter.run(request)


if __name__ == "__main__":
    unittest.main(verbosity=2)
