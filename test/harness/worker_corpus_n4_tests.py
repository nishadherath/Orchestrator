#!/usr/bin/env python3
"""Qualify all 24 new actor packages against evaluator-only oracles."""
from __future__ import annotations

import ast
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import worker_corpus  # noqa: E402
import worker_evaluation as evaluation  # noqa: E402

ALTERNATIVES = {
    "D01": "layers = [(name, data.get(name)) for name in ('cli', 'environment', 'file', 'default')]\n"
           "    chosen = next(((key, val) for key, val in layers if val is not None), (None, None))\n"
           "    return dict(source=chosen[0], value=chosen[1])",
    "D03": "attempts = []\n    index = 0\n"
           "    while index < data['max_attempts'] and index < len(data['statuses']):\n"
           "        status = data['statuses'][index]\n        attempts.append(status)\n"
           "        index += 1\n"
           "        if status != 503 or data['method'] not in ('GET', 'PUT', 'DELETE'):\n"
           "            break\n"
           "    return dict(attempts=attempts, final=attempts[-1] if attempts else None)",
    "D05": "seen = set()\n    accepted = []\n"
           "    for row in data['rows']:\n"
           "        if row['id'] in seen:\n            return dict(committed=[], error='duplicate-id')\n"
           "        seen.add(row['id'])\n        accepted.append(row['id'])\n"
           "    if any(row['amount'] < 0 for row in data['rows']):\n"
           "        return dict(committed=[], error='negative-amount')\n"
           "    return dict(committed=accepted, error=None)",
    "D07": "tenants = {}\n    answers = []\n"
           "    for op in data['operations']:\n"
           "        own = tenants.setdefault(op['tenant'], {})\n"
           "        if op['kind'] == 'put':\n            own[op['key']] = op['value']\n"
           "        else:\n            answers.append(own.get(op['key']))\n"
           "    return dict(reads=answers)",
    "D09": "unchanged = data.get('if_none_match') == data['etag']\n"
           "    return dict(status=304 if unchanged else 200, "
           "body=None if unchanged else data['body'], etag=data['etag'])",
    "D11": "ranking = sorted(data['measurements'], "
           "key=lambda m: m['count'] * m['ms_each'], reverse=True)\n"
           "    top = ranking[0]['stage']\n"
           "    return dict(bottleneck=top, rejected_premise=top != data['named_hotspot'])",
}


class PublicOnlyFake:
    """Offline actor that sees the public check but no catalogue or oracle."""

    offline_fake = True
    calls = 0

    def capability(self, root):
        return {"actor_root": str(root.resolve()), "configured": True,
                "supported_cells": ["worker-sonnet-low", "worker-opus-high"],
                "budget_enforced": True}

    def run(self, request):
        type(self).calls += 1
        actor = request.actor_root
        source = (actor / "app.py").read_text(encoding="utf-8")
        # The already-correct no-change incident needs no edit. For all other
        # tasks, a public-output copy is a deliberately inadequate worker.
        if "return {'action': 'no-code-change'" not in source:
            assertion = ast.parse((actor / "public_check.py").read_text(encoding="utf-8")).body[1]
            expected = ast.literal_eval(assertion.test.comparators[0])
            (actor / "app.py").write_text(
                "import json, sys\n"
                f"def solve(data):\n    return {expected!r}\n"
                "if __name__ == '__main__':\n"
                "    print(json.dumps(solve(json.loads(sys.stdin.readline()))))\n",
                encoding="utf-8")
        model = ("claude-opus-5" if request.requested_cell == "worker-opus-high"
                 else "claude-sonnet-5")
        return {"admission_token": request.admission_token,
                "invocation_id": request.invocation_id, "revision_id": request.revision_id,
                "decision_digest": request.decision_digest,
                "intent_digest": request.intent_digest,
                "requested_cell": request.requested_cell,
                "actual_model": model, "identity_valid": True, "child_models": [],
                "effort_evidence": ("cli-argument:high" if request.requested_cell == "worker-opus-high"
                                    else "cli-argument:low"),
                "status": "completed", "terminal": True, "writer_stopped": True,
                "cost_usd": 0.05,
                "usage": {"cost_usd": 0.05, "currency": "USD",
                          "cost_source": "offline_fixture"}}


class CorpusTests(unittest.TestCase):
    def test_verified_partial_and_clarification_are_scored_without_completion(self):
        catalogue = {row["id"]: row for row in evaluation.load_catalogue(
            worker_corpus.DESTINATION)["tasks"]}
        with tempfile.TemporaryDirectory(prefix="worker-n4-partial-") as folder:
            variants = {
                "D12": "return {'action': 'clarify', 'missing': 'retention_days'}",
                "R12": ("passed = sum(bool(x) for x in data['local_checks'])\n"
                        "    return {'status': 'partial' if data.get('external_key') is None "
                        "else 'complete', 'local_passed': passed, "
                        "'blocked_on': 'external_key' if data.get('external_key') is None else None}"),
            }
            for ident, body in variants.items():
                with self.subTest(task=ident):
                    task = catalogue[ident]
                    actor = Path(folder) / ident
                    shutil.copytree(worker_corpus.DESTINATION / task["actor"], actor)
                    (actor / "app.py").write_text(
                        "import json, sys\n"
                        f"def solve(data):\n    {body}\n"
                        "if __name__ == '__main__':\n"
                        "    print(json.dumps(solve(json.loads(sys.stdin.readline()))))\n",
                        encoding="utf-8")
                    grade = evaluation._grade(worker_corpus.DESTINATION / task["oracle"],
                                              actor, "failed")
                    self.assertFalse(grade["acceptance"])
                    self.assertGreater(grade["quality"], 0)
                    self.assertLess(grade["quality"], 100)
                    self.assertFalse(grade["false_success"])

    def test_independent_alternative_per_family(self):
        catalogue = {row["id"]: row for row in evaluation.load_catalogue(
            worker_corpus.DESTINATION)["tasks"]}
        with tempfile.TemporaryDirectory(prefix="worker-n4-alt-") as folder:
            for ident, body in ALTERNATIVES.items():
                with self.subTest(task=ident):
                    task = catalogue[ident]
                    actor = Path(folder) / ident
                    shutil.copytree(worker_corpus.DESTINATION / task["actor"], actor)
                    (actor / "app.py").write_text(
                        "import json, sys\n"
                        f"def solve(data):\n    {body}\n"
                        "if __name__ == '__main__':\n"
                        "    print(json.dumps(solve(json.loads(sys.stdin.readline()))))\n",
                        encoding="utf-8")
                    grade = evaluation._grade(worker_corpus.DESTINATION / task["oracle"],
                                              actor, "accepted")
                    self.assertTrue(grade["acceptance"], grade)

    def test_full_provider_free_campaign_uses_public_actor_input_only(self):
        with tempfile.TemporaryDirectory(prefix="worker-n4-full-") as folder:
            output = Path(folder) / "runs"
            manifest = evaluation.freeze(worker_corpus.DESTINATION)
            PublicOnlyFake.calls = 0
            runner = evaluation.OfflineCampaign(
                worker_corpus.DESTINATION, manifest, output,
                lambda actor: PublicOnlyFake())
            state = runner.run()
            self.assertEqual("complete", state["status"], state.get("block"))
            self.assertEqual(24, len(state["results"]))
            self.assertEqual(24, PublicOnlyFake.calls)
            self.assertEqual(1, sum(row["grade"]["acceptance"] for row in state["results"]))
            self.assertEqual(state, runner.run())
            self.assertEqual(24, PublicOnlyFake.calls)
            self.assertFalse(list(output.rglob("*oracle*")))

    def test_full_inventory_and_generated_file_parity(self):
        planned = worker_corpus.planned_files()
        self.assertEqual(24, len(worker_corpus.TASKS))
        self.assertEqual(121, len(planned))
        for name, content in planned.items():
            self.assertEqual(content, (worker_corpus.DESTINATION / name).read_text(encoding="utf-8"))
        catalogue = evaluation.load_catalogue(worker_corpus.DESTINATION)
        self.assertEqual(24, len(catalogue["tasks"]))
        self.assertEqual(12, sum(task["split"] == "development" for task in catalogue["tasks"]))
        self.assertEqual(12, sum(task["split"] == "reserved" for task in catalogue["tasks"]))
        frozen = evaluation.freeze(worker_corpus.DESTINATION)
        evaluation.validate_manifest(worker_corpus.DESTINATION, frozen)
        self.assertEqual(121, len(frozen["corpus_files"]))

    def test_reference_and_happy_path_shortcut(self):
        catalogue = evaluation.load_catalogue(worker_corpus.DESTINATION)
        with tempfile.TemporaryDirectory(prefix="worker-n4-corpus-") as folder:
            base = Path(folder)
            for task in catalogue["tasks"]:
                with self.subTest(task=task["id"]):
                    source = worker_corpus.DESTINATION / task["actor"]
                    actor = base / task["id"]
                    shutil.copytree(source, actor)
                    oracle = worker_corpus.DESTINATION / task["oracle"]
                    original = evaluation._grade(oracle, actor, "accepted")
                    if task["id"] == "R11":
                        self.assertTrue(original["acceptance"])
                    else:
                        self.assertFalse(original["acceptance"])

                    # A copied public label or success report cannot implement
                    # behaviour; a constant public answer should also fail the
                    # independent hidden cases.
                    (actor / "RESULT.md").write_text("Complete: all public labels copied")
                    public_case = next(item for item in worker_corpus.TASKS
                                       if item["id"] == task["id"])
                    expected = worker_corpus.worker_oracles.expected(
                        task["id"], public_case["public"])
                    if task["id"] == "R11":
                        (actor / "app.py").write_text((actor / "app.py").read_text() + "\n# unnecessary edit\n")
                    else:
                        (actor / "app.py").write_text(
                            "import json, sys\n"
                            f"def solve(data):\n    return {expected!r}\n"
                            "if __name__ == '__main__':\n"
                            "    print(json.dumps(solve(json.loads(sys.stdin.readline()))))\n")
                    public = subprocess.run([sys.executable, "public_check.py"],
                                            cwd=actor, capture_output=True, text=True, timeout=10)
                    self.assertEqual(0, public.returncode, public.stderr[-400:])
                    shortcut = evaluation._grade(oracle, actor, "accepted")
                    self.assertFalse(shortcut["acceptance"])
                    self.assertTrue(shortcut["false_success"])
                    if task["id"] == "R11":
                        self.assertTrue(shortcut["critical_error"])
                    # The evaluator's known-correct reference exercises the
                    # JSON-line interface. It is not an independent solution.
                    if task["id"] != "R11":
                        shutil.copyfile(ROOT / "tools" / "worker_oracles.py",
                                        actor / "reference_impl.py")
                        (actor / "app.py").write_text(
                            "import json, sys\nfrom reference_impl import expected\n"
                            f"def solve(data):\n    return expected({task['id']!r}, data)\n"
                            "if __name__ == '__main__':\n"
                            "    print(json.dumps(solve(json.loads(sys.stdin.readline()))))\n")
                        reference = evaluation._grade(oracle, actor, "accepted")
                        self.assertTrue(reference["acceptance"])
                        self.assertEqual(100, reference["quality"])
                        self.assertFalse(reference["critical_error"])


if __name__ == "__main__":
    unittest.main()
