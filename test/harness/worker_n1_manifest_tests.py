#!/usr/bin/env python3
"""Keep historical Controller evidence and current fake campaigns distinct."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import controller_evaluation as campaign  # noqa: E402
import controller_matrix_runtime as runtime  # noqa: E402

HISTORICAL_REF = "a70e311"


class ManifestSplitTests(unittest.TestCase):
    def test_historical_manifest_binds_pinned_source_bytes(self):
        historical = json.loads(campaign.MATRIX_MANIFEST.read_text(encoding="utf-8"))
        unsigned = {k: v for k, v in historical.items() if k != "manifest_sha256"}
        self.assertEqual(campaign.digest(unsigned), historical["manifest_sha256"])
        for relative, expected in historical["bound_files"].items():
            with self.subTest(path=relative):
                proc = subprocess.run(["git", "-c", f"safe.directory={ROOT}",
                                       "show", f"{HISTORICAL_REF}:{relative}"],
                                      cwd=ROOT, capture_output=True, timeout=20)
                self.assertEqual(0, proc.returncode, proc.stderr.decode(errors="replace"))
                self.assertEqual(expected, hashlib.sha256(proc.stdout).hexdigest())

    def test_fresh_fake_manifest_validates_current_files_and_rejects_mutation(self):
        historical = json.loads(campaign.MATRIX_MANIFEST.read_text(encoding="utf-8"))
        fresh = campaign._manifest("matrix-calibration", historical["episodes"], 48.75)
        runtime.validate_manifest(fresh)
        tampered = json.loads(json.dumps(fresh))
        first = next(iter(tampered["bound_files"]))
        tampered["bound_files"][first] = "0" * 64
        tampered["manifest_sha256"] = campaign.digest(
            {k: v for k, v in tampered.items() if k != "manifest_sha256"})
        with self.assertRaises(runtime.MatrixRuntimeError):
            runtime.validate_manifest(tampered)
        with tempfile.TemporaryDirectory(prefix="n1-current-campaign-") as raw:
            work = Path(raw)
            manifest = work / "fresh-fake-manifest.json"
            manifest.write_text(json.dumps(fresh), encoding="utf-8")
            authorisation = {"schema_version": 1, "decision": "approved",
                             "manifest_sha256": fresh["manifest_sha256"],
                             "maximum_authorised_usd": 48.75,
                             "approved_at": "offline-test", "approved_by": "offline-test"}
            auth_path = work / "offline-authorisation.json"
            auth_path.write_text(json.dumps(authorisation), encoding="utf-8")
            calls = []
            def transport(command, cwd, env, timeout):
                calls.append(command)
                model = command[command.index("--model") + 1]
                stream = "\n".join(json.dumps(row) for row in (
                    {"type": "assistant", "parent_tool_use_id": None,
                     "message": {"model": model, "content": []}},
                    {"type": "result", "subtype": "success", "result": "fake",
                     "total_cost_usd": 0.01, "usage": {"input_tokens": 10, "output_tokens": 5},
                     "modelUsage": {model: {"costUSD": 0.01}}})) + "\n"
                return subprocess.CompletedProcess(command, 0, stream, "")
            result = runtime.execute(manifest, auth_path, work / "run",
                                     runtime.MatrixAdapter(transport))
            self.assertEqual("completed", result["status"])
            self.assertEqual(60, len(calls))
            self.assertEqual(0.6, result["known_spend_usd"])


if __name__ == "__main__":
    unittest.main()
