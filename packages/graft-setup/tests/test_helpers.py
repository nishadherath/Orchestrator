"""Behavioural tests over isolated roots, failure modes and JSON-RPC transport."""
from __future__ import annotations

import importlib.util
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

PACKAGE = Path(__file__).resolve().parents[1]
SCRIPTS = PACKAGE / "graft-setup/scripts"
sys.path.insert(0, str(SCRIPTS))
import graft_common as common
from probe_mcp import Client, structural_fresh
import refresh as refresh_module

FAKE = Path(__file__).with_name("fake_graft.py")


class Helpers(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="graft portable & spaces ")
        self.root = Path(self.temp.name)
        (self.root / "src").mkdir()
        (self.root / "src/app.py").write_text("def compute():\n    return 'distinctive literal'\n", encoding="utf-8")
        self.command = [sys.executable, str(FAKE)]

    def tearDown(self):
        self.temp.cleanup()

    def test_acceptance_rejects_interoperability_runtime(self):
        spec = importlib.util.spec_from_file_location("integration_acceptance", PACKAGE / "tests/integration.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        output = self.root / "acceptance.json"
        observed = "linux" if os.name == "nt" else "win32"
        probe = subprocess.CompletedProcess([], 0, json.dumps({"platform": observed}), "")
        with patch.object(sys, "argv", ["integration.py", "--node", "selected-node", "--output", str(output)]), \
             patch.object(module.subprocess, "run", return_value=probe), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(module.main(), 1)
        report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(report["steps"], [])
        self.assertIn("platform differs", report["error"])
        self.assertFalse((self.root / ".graft").exists())

    def cli(self, name, *extra, mode=""):
        env = dict(os.environ, FAKE_GRAFT_MODE=mode)
        result = subprocess.run([sys.executable, str(SCRIPTS / name), "--repo", str(self.root),
            "--launcher-json", json.dumps(self.command), *extra], capture_output=True,
            text=True, encoding="utf-8", env=env, timeout=20)
        return result, json.loads(result.stdout)

    def refresh(self, *extra, mode=""):
        return self.cli("refresh.py", "--only-dir", "src", *extra, mode=mode)

    def test_scope_and_literal_paths_with_spaces_and_metacharacters(self):
        result, report = self.refresh()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(report["graph"]["files"], 1)
        self.assertEqual(report["scope"], ["src"])
        self.assertEqual(report["freshness"]["semantic"], "absent")
        self.assertFalse((self.root / ".ignore").exists())

    def test_dry_run_does_not_mutate_project(self):
        before = sorted(p.relative_to(self.root) for p in self.root.rglob("*"))
        result, report = self.refresh("--dry-run")
        self.assertEqual(result.returncode, 0)
        self.assertTrue(report["dry_run"])
        self.assertEqual(before, sorted(p.relative_to(self.root) for p in self.root.rglob("*")))

    def test_backups_and_clean_meaning_fallback_preserve_wiring(self):
        self.refresh()
        cache = self.root / "graft"
        old = (cache / ".graph/wiring.json").read_bytes()
        (cache / "manifest.json").write_text('{"old": true}')
        stamp = {"version": "0.21.1", "hosts": ["agents"], "opts": {"global": False}}
        (cache / ".cache/wiring-stamp.json").write_text(json.dumps(stamp))
        result, value = self.refresh("--clean")
        self.assertEqual(result.returncode, 0, value)
        backup = Path(value["backup"])
        self.assertEqual(old, (backup / ".graph/wiring.json").read_bytes())
        self.assertTrue((backup / "manifest.json").is_file())
        self.assertFalse((cache / "manifest.json").exists())
        self.assertEqual(stamp, json.loads((cache / ".cache/wiring-stamp.json").read_text()))

    def test_failed_build_empty_missing_fingerprint_and_drift_preserve_active(self):
        self.refresh()
        cache = self.root / "graft/.graph/wiring.json"
        original = cache.read_bytes()
        for mode in ("fail-build", "empty", "no-fingerprint", "structural-stale", "outside-scope"):
            with self.subTest(mode=mode):
                result, value = self.refresh(mode=mode)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(value["ok"])
                self.assertEqual(original, cache.read_bytes())
                self.assertFalse((self.root / ".graft/skill-refresh.lock").exists())

    def test_semantic_failure_is_not_conflated_with_structure(self):
        result, value = self.refresh(mode="semantic-stale")
        self.assertEqual(result.returncode, 0)
        self.assertTrue(value["freshness"]["structural_fresh"])
        self.assertEqual(value["freshness"]["semantic"], "stale")

    def test_publication_failure_restores_old_cache_or_reports_preserved_backup(self):
        for restoration_blocked in (False, True):
            with self.subTest(restoration_blocked=restoration_blocked):
                self.refresh()
                cache = self.root / "graft"
                original = (cache / ".graph/wiring.json").read_bytes()
                rename = Path.rename

                def blocked(path, destination):
                    if path.name.startswith("staging-") or (restoration_blocked and path.parent.name == "backups"):
                        raise PermissionError("simulated atomic rename rejection")
                    return rename(path, destination)

                output = io.StringIO()
                argv = ["refresh.py", "--repo", str(self.root), "--only-dir", "src", "--launcher-json", json.dumps(self.command)]
                with patch.object(sys, "argv", argv), patch.object(Path, "rename", blocked), contextlib.redirect_stdout(output):
                    code = refresh_module.main()
                value = json.loads(output.getvalue())
                self.assertEqual(code, 1)
                preserved = Path(value["backup"]) if restoration_blocked else cache
                self.assertEqual(original, (preserved / ".graph/wiring.json").read_bytes())
                if restoration_blocked:
                    self.assertFalse(cache.exists())
                    preserved.rename(cache)

    def test_source_directory_is_never_replaced_as_cache(self):
        result, value = self.refresh("--cache", "src")
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((self.root / "src/app.py").is_file())
        self.assertFalse((self.root / ".graft").exists())

    def test_traversal_root_and_escaped_links_are_rejected(self):
        for value in ("../other", "/absolute", "C:/absolute", ".", "src/../other"):
            with self.subTest(value=value), self.assertRaises(common.GraftError):
                common.local_path(self.root, value)
        for root in (Path.home(), Path(self.root.anchor)):
            with self.assertRaises(common.GraftError):
                common.repo_path(str(root))
        external = self.root.parent / (self.root.name + " sibling")
        external.mkdir()
        try:
            try:
                (self.root / "escape").symlink_to(external, target_is_directory=True)
            except OSError:
                self.skipTest("Host does not permit creating test symlinks")
            with self.assertRaises(common.GraftError):
                common.local_path(self.root, "escape/cache")
        finally:
            external.rmdir()

    def test_foreign_refresh_locks_are_not_broken(self):
        self.refresh()
        for relative in (".graft/skill-refresh.lock", "graft/.cache/.sync.lock"):
            path = self.root / relative
            path.write_text("owned by another process")
            result, value = self.refresh()
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(path.read_text(), "owned by another process")
            path.unlink()

    def test_linked_cache_is_not_followed_for_diagnostics(self):
        self.refresh()
        alias = self.root / "alias-cache"
        try:
            alias.symlink_to(self.root / "graft", target_is_directory=True)
        except OSError:
            self.skipTest("Host does not permit creating test symlinks")
        with self.assertRaises(common.GraftError):
            common.graph_summary(alias, self.root)

    def test_wrong_fingerprint_identity_is_not_reused(self):
        self.refresh()
        old = self.root / "graft/.cache/fingerprint.old.json"
        old.write_text(json.dumps({"files": {}, "onlyDirs": ["everything"]}))
        result, value = self.refresh()
        self.assertEqual(result.returncode, 0, value)
        self.assertEqual([p["only_dirs"] for p in value["graph"]["fingerprints"]], [["src"]])

    def test_no_paid_option_and_child_overrides_are_local(self):
        with patch.dict(os.environ, {"GRAFT_API_KEY": "sentinel", "GRAFT_DIR": "wrong", "GRAFT_NO_REFRESH": "1"}):
            env = common.child_env(refresh=True, cache=self.root / "graft")
            self.assertEqual(env["GRAFT_API_KEY"], "")
            self.assertEqual(env["GRAFT_DIR"], str(self.root / "graft"))
            self.assertEqual(env["GRAFT_NO_REFRESH"], "0")
            self.assertEqual(os.environ["GRAFT_API_KEY"], "sentinel")
        with self.assertRaises(common.GraftError):
            common.launcher(json.dumps(["graft", "--deep"]))

    def test_timeout_has_bounded_actionable_failure(self):
        start = time.monotonic()
        result, value = self.refresh("--timeout", "0.1", mode="slow")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("timed out", value["error"])
        self.assertLess(time.monotonic() - start, 2)

    def test_mcp_protocol_failures_and_deadline_under_notification_spam(self):
        for mode in ("malformed", "closed", "notifications"):
            with self.subTest(mode=mode), patch.dict(os.environ, {"FAKE_GRAFT_MODE": mode}):
                client = Client([*self.command, "mcp"], self.root, self.root / "graft", False)
                try:
                    start = time.monotonic()
                    with self.assertRaises(common.GraftError):
                        client.call("initialize", {}, 0.2)
                    self.assertLess(time.monotonic() - start, 2)
                finally:
                    client.close()

    def test_mcp_stderr_is_drained(self):
        with patch.dict(os.environ, {"FAKE_GRAFT_MODE": "stderr"}):
            client = Client([*self.command, "mcp"], self.root, self.root / "graft", False)
            try:
                self.assertEqual(client.call("initialize", {}, 3)["serverInfo"]["name"], "graft")
            finally:
                client.close()

    def test_startup_wiring_upkeep_requires_review(self):
        (self.root / "AGENTS.md").write_text("<!-- graft:start -->\nmanaged\n")
        self.assertTrue(common.startup_review_needed(self.root, self.root / "graft", "0.21.1"))
        result, value = self.cli("probe_mcp.py", "--file", "src/app.py", "--symbol", "compute", "--needle", "distinctive")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("startup", value["error"])

    def test_freshness_false_positive_and_semantic_only_drift(self):
        self.assertFalse(structural_fresh("graft check: OK"))
        self.assertFalse(structural_fresh("graph check: UNKNOWN"))
        self.assertFalse(structural_fresh("graph check: STALE\nadded (1):\nnew.py"))
        self.assertTrue(structural_fresh("graft check: NO GRAPH\ngraph check: OK"))
        self.assertTrue(structural_fresh("graph check: STALE\nstale summaries (1):\nold"))

    def test_release_determinism_no_caches_and_integrity(self):
        spec = importlib.util.spec_from_file_location("graft_release_test", PACKAGE / "build_package.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        first = module.release_bytes()
        self.assertEqual(first, module.release_bytes())
        import hashlib
        import io
        import zipfile
        manifest = json.loads(first[1])
        self.assertEqual(hashlib.sha256(first[0]).hexdigest(), manifest["archive_sha256"])
        with zipfile.ZipFile(io.BytesIO(first[0])) as archive:
            self.assertEqual(set(archive.namelist()), set(manifest["files"]))
            self.assertTrue(all(name.startswith("graft-setup/") and ".." not in Path(name).parts for name in archive.namelist()))


if __name__ == "__main__":
    unittest.main()
