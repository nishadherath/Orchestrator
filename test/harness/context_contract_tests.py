#!/usr/bin/env python3
"""Offline Stage 5 prompt-size and mandatory-contract checks."""
from __future__ import annotations

import importlib.util
import json
import math
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_dist = load_module("build_dist_context", TOOLS / "build_dist.py")
context_inventory = load_module("context_inventory_contract", TOOLS / "context_inventory.py")
BASELINE = json.loads((ROOT / "docs" / "CONTEXT-BASELINE-2026-09-17.json").read_text(encoding="utf-8"))


class ContextContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.planned = build_dist.planned_files("context-test")
        cls.core = (ROOT / "src" / "ORCHESTRATOR_CORE.md").read_text(encoding="utf-8")
        cls.template = (ROOT / "src" / "CLAUDE.template.md").read_text(encoding="utf-8")
        cls.persona = (ROOT / "src" / "WORKER_PERSONA.md").read_text(encoding="utf-8")
        cls.roles = (ROOT / "src" / "System" / "ROLES.md").read_text(encoding="utf-8")

    def test_consumer_standing_surface_is_at_least_twenty_percent_smaller(self) -> None:
        current = self.planned[ROOT / "dist" / "CLAUDE.template.md"] + self.planned[ROOT / "dist" / "ORCHESTRATOR.md"]
        current_tokens = math.ceil(len(current) / 4)
        baseline = BASELINE["surfaces"]["consumer_orchestrator_standing"]["estimated_tokens"]
        self.assertLessEqual(current_tokens, math.floor(baseline * 0.80))

    def test_core_retains_mandatory_behaviour(self) -> None:
        required = [
            "graft_check_freshness",
            "tools/route.py --from-line",
            "acceptance-contract.example.json",
            "tools/route.py --spawn",
            "Never pass `model`",
            "tools/route.py --project <root> --record",
            "--review-acceptance",
            "tools/system_controller.py",
            "tools/handoff.py new",
            "tools/handoff.py check",
            "tools/route.py --recover",
            "ORCHESTRATOR-REFERENCE.md",
        ]
        for marker in required:
            self.assertIn(marker, self.core)
        self.assertLess(self.core.index("tools/route.py --spawn"), self.core.index("For a worker, set"))

    def test_each_execution_context_keeps_its_contract(self) -> None:
        for marker in ("graft_check_freshness", "tools/handoff.py new", "ORCHESTRATOR.md"):
            self.assertIn(marker, self.template)
        for marker in ("graft_check_freshness", "acceptance criteria", "file boundaries", "permission prompts"):
            self.assertIn(marker, self.persona)
        for marker in ("graft_check_freshness", "Records in, records out", "ledger version", "No artefact, no measurement"):
            self.assertIn(marker, self.roles)

    def test_reference_is_shipped_and_core_names_load_triggers(self) -> None:
        reference_path = ROOT / "dist" / "ORCHESTRATOR-REFERENCE.md"
        reference = self.planned[reference_path]
        self.assertIn("## Acceptance recovery", reference)
        self.assertIn("## Controller budget recovery", reference)
        self.assertIn("## Handoffs", reference)
        self.assertIn("stop/resume semantics", self.core)
        self.assertIn("charge reconciliation", self.core)

    def test_rationale_comparison_bundle_remains_available(self) -> None:
        target = ROOT / "dist-with-rationale"
        planned = build_dist.planned_files("context-test-with-rationale", target, True)
        self.assertIn("<!-- rationale:start -->", planned[target / "ORCHESTRATOR.md"])

    def test_measurement_tool_labels_estimates_and_limits(self) -> None:
        sample = context_inventory.measure("abcdefgh")
        self.assertEqual(sample["estimated_tokens_chars_div_4"], 2)
        self.assertIn("not tokenizer counts", BASELINE["method"])
        self.assertTrue(any("does not prove" in item for item in BASELINE["limits"]))


if __name__ == "__main__":
    unittest.main()
