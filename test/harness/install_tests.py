#!/usr/bin/env python3
"""Offline Stage 6 install, upgrade, uninstall and rollback regressions."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import build_dist  # noqa: E402
import install  # noqa: E402


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="orchestrator install ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bundle = self.root / "bundle"
        self.project = self.root / "consumer project with spaces"
        self.project.mkdir()
        self.stage_bundle(self.bundle, "test-v1")

    @staticmethod
    def stage_bundle(path: Path, version: str) -> None:
        files = build_dist.planned_files(version, path)
        for target, content in files.items():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8", newline="\n")

    def apply(self, bundle: Path | None = None, *, graft: bool = False) -> tuple[install.Transaction, dict]:
        command = "graft-test-command" if graft else None
        args = ["mcp", "."] if graft else []
        preview = install.plan_apply(bundle or self.bundle, self.project, command, args)
        tx = install.plan_apply(bundle or self.bundle, self.project, command, args)
        self.assertEqual(preview.backup_id, tx.backup_id)
        self.assertFalse(tx.conflicts, tx.public())
        return tx, install.commit(tx)

    def test_clean_install_repeat_lifecycle_diagnostics_and_rollback(self):
        tx, result = self.apply()
        self.assertEqual(result["result"], "APPLIED")
        self.assertEqual(install.status(self.project)["result"], "INSTALLED")
        self.assertEqual((self.project / ".claude" / "orchestrator-install" / "backups" /
                          ".gitignore").read_text(encoding="utf-8"), "*\n!.gitignore\n")

        repeat = install.plan_apply(self.bundle, self.project, None, [])
        self.assertEqual(repeat.public()["result"], "NO_CHANGES")
        self.assertEqual(install.commit(repeat)["result"], "NO_CHANGES")

        route = self.project / "tools" / "route.py"
        self.assertEqual(subprocess.run([sys.executable, str(route), "--selftest"], cwd=self.project,
                                        capture_output=True, text=True).returncode, 0)
        (self.project / "tests").mkdir()
        (self.project / "tests" / "protected.py").write_text("assert True\n", encoding="utf-8")
        (self.project / "result.txt").write_text("done\n", encoding="utf-8")
        contract = self.project / "acceptance.json"
        contract.write_text(json.dumps({
            "version": 1, "kind": "command", "criteria": ["fixture passes"],
            "constraints": ["protected file stays unchanged"], "required_outputs": ["result.txt"],
            "protected_paths": ["tests/protected.py"],
            "command": [sys.executable, "-c", "raise SystemExit(0)"], "rubric": [], "timeout_s": 10,
        }), encoding="utf-8")
        line = "assessment: mechanical, short, contained; self_directed: false; prior_failure: none"
        spawned = subprocess.run([
            sys.executable, str(route), "--spawn", "--project", str(self.project), "--from-line", line,
            "--task-slug", "installed-fixture", "--first-cell", "worker-sonnet-low",
            "--worker-name", "fixture", "--acceptance-contract", str(contract),
        ], cwd=self.project, capture_output=True, text=True)
        self.assertEqual(spawned.returncode, 0, spawned.stderr)
        ident = spawned.stdout.strip().splitlines()[-1]
        recorded = subprocess.run([
            sys.executable, str(route), "--record", "--pending", ident, "--project", str(self.project),
            "--outcome", "pass", "--cost-usd", "0", "--wall-clock-s", "1",
        ], cwd=self.project, capture_output=True, text=True)
        self.assertEqual(recorded.returncode, 0, recorded.stderr)

        pending = subprocess.run([
            sys.executable, str(route), "--spawn", "--project", str(self.project), "--from-line", line,
            "--task-slug", "recovery-fixture", "--first-cell", "worker-sonnet-low",
            "--worker-name", "fixture-pending", "--acceptance-contract", str(contract),
        ], cwd=self.project, capture_output=True, text=True)
        self.assertEqual(pending.returncode, 0, pending.stderr)
        recovered = subprocess.run([sys.executable, str(route), "--recover", "--project", str(self.project)],
                                   cwd=self.project, capture_output=True, text=True)
        self.assertEqual(recovered.returncode, 0, recovered.stderr)
        self.assertIn("pending", recovered.stdout.lower())

        preflight = subprocess.run([sys.executable, "preflight.py", "--json", "--status", "--explain"],
                                   cwd=self.project, capture_output=True, text=True)
        report = json.loads(preflight.stdout)
        self.assertEqual(report["schema_version"], 2)
        self.assertEqual(report["diagnostics"]["routing"]["unresolved_attempts"], 1)
        self.assertEqual(report["diagnostics"]["acceptance"]["counts"]["pass"], 1)

        public, _, _, payload = install.rollback_plan(self.project, tx.backup_id)
        self.assertFalse(public["conflicts"], public)
        self.assertEqual(install.commit_rollback(public, self.project, payload)["result"], "ROLLED_BACK")
        self.assertFalse((self.project / "ORCHESTRATOR.md").exists())
        self.assertTrue((self.project / ".claude" / "routing-ledger.jsonl").exists())

    def test_preserves_unrelated_configuration_through_uninstall_and_rollback(self):
        (self.project / ".claude").mkdir()
        settings = {"theme": "dark", "permissions": {"allow": ["Read(*)"]},
                    "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": []}]}}
        (self.project / ".claude" / "settings.json").write_text(json.dumps(settings), encoding="utf-8")
        (self.project / ".mcp.json").write_text(json.dumps({"mcpServers": {"other": {"command": "other"}}}),
                                                 encoding="utf-8")
        (self.project / "CLAUDE.md").write_text("# Existing\n\nKeep this.\n", encoding="utf-8")
        self.apply(graft=True)
        merged = json.loads((self.project / ".claude" / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual(merged["theme"], "dark")
        self.assertIn("Read(*)", merged["permissions"]["allow"])
        mcp = json.loads((self.project / ".mcp.json").read_text(encoding="utf-8"))
        self.assertIn("other", mcp["mcpServers"])
        self.assertIn("graft", mcp["mcpServers"])

        merged["fontSize"] = 14
        (self.project / ".claude" / "settings.json").write_text(json.dumps(merged), encoding="utf-8")
        uninstall_tx = install.plan_uninstall(self.project)
        self.assertFalse(uninstall_tx.conflicts, uninstall_tx.public())
        install.commit(uninstall_tx)
        after = json.loads((self.project / ".claude" / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual(after, {"fontSize": 14, "hooks": settings["hooks"],
                                 "permissions": {"allow": ["Read(*)"]}, "theme": "dark"})
        self.assertNotIn(install.CLAUDE_BEGIN, (self.project / "CLAUDE.md").read_text(encoding="utf-8"))
        self.assertIn("Keep this.", (self.project / "CLAUDE.md").read_text(encoding="utf-8"))

        public, _, _, payload = install.rollback_plan(self.project, uninstall_tx.backup_id)
        self.assertFalse(public["conflicts"], public)
        install.commit_rollback(public, self.project, payload)
        restored = json.loads((self.project / ".claude" / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual(restored["fontSize"], 14)
        self.assertIn("Bash(python3 *)", restored["permissions"]["allow"])

    def test_existing_scalar_and_file_are_conflicts(self):
        (self.project / ".claude").mkdir()
        settings_path = self.project / ".claude" / "settings.json"
        settings_path.write_text(json.dumps({"statusLine": {"type": "command", "command": "mine"}}),
                                 encoding="utf-8")
        (self.project / "ORCHESTRATOR.md").write_text("mine\n", encoding="utf-8")
        before = settings_path.read_bytes()
        tx = install.plan_apply(self.bundle, self.project, None, [])
        paths = {item["path"] for item in tx.conflicts}
        self.assertIn("ORCHESTRATOR.md", paths)
        self.assertIn(".claude/settings.json:statusLine", paths)
        self.assertEqual(settings_path.read_bytes(), before)

    def test_malformed_settings_refuses_without_touching_target(self):
        (self.project / ".claude").mkdir()
        path = self.project / ".claude" / "settings.json"
        path.write_text("{broken", encoding="utf-8")
        tx = install.plan_apply(self.bundle, self.project, None, [])
        self.assertTrue(tx.conflicts)
        self.assertEqual(path.read_text(encoding="utf-8"), "{broken")
        self.assertFalse((self.project / "ORCHESTRATOR.md").exists())

    def test_upgrade_and_rollback_restore_previous_bundle(self):
        _, _ = self.apply()
        before = (self.project / "ORCHESTRATOR.md").read_bytes()
        bundle2 = self.root / "bundle-v2"
        shutil.copytree(self.bundle, bundle2)
        changed = (bundle2 / "ORCHESTRATOR.md").read_text(encoding="utf-8") + "\nUpgrade fixture.\n"
        (bundle2 / "ORCHESTRATOR.md").write_text(changed, encoding="utf-8", newline="\n")
        manifest = json.loads((bundle2 / install.MANIFEST_NAME).read_text(encoding="utf-8"))
        manifest["bundle_version"] = "test-v2"
        manifest["files"]["ORCHESTRATOR.md"] = install.sha256_bytes((bundle2 / "ORCHESTRATOR.md").read_bytes())
        (bundle2 / install.MANIFEST_NAME).write_text(json.dumps(manifest), encoding="utf-8")
        upgrade = install.plan_apply(bundle2, self.project, None, [])
        self.assertFalse(upgrade.conflicts, upgrade.public())
        install.commit(upgrade)
        self.assertIn("Upgrade fixture", (self.project / "ORCHESTRATOR.md").read_text(encoding="utf-8"))
        public, _, _, payload = install.rollback_plan(self.project, upgrade.backup_id)
        self.assertFalse(public["conflicts"], public)
        install.commit_rollback(public, self.project, payload)
        self.assertEqual((self.project / "ORCHESTRATOR.md").read_bytes(), before)
        self.assertEqual(install.status(self.project)["bundle_version"], "test-v1")

    def test_rollback_refuses_owned_drift(self):
        tx, _ = self.apply()
        path = self.project / "ORCHESTRATOR.md"
        path.write_text(path.read_text(encoding="utf-8") + "edited\n", encoding="utf-8")
        public, _, _, _ = install.rollback_plan(self.project, tx.backup_id)
        self.assertEqual(public["result"], "CONFLICT")
        self.assertIn("edited", path.read_text(encoding="utf-8"))

    def test_tampered_bundle_is_rejected(self):
        (self.bundle / "ORCHESTRATOR.md").write_text("tampered\n", encoding="utf-8")
        with self.assertRaises(install.InstallError):
            install.plan_apply(self.bundle, self.project, None, [])


if __name__ == "__main__":
    unittest.main()
