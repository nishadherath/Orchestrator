#!/usr/bin/env python3
"""Provider-free root tests for the WSL subscription credential handoff."""
from __future__ import annotations

import json
import os
import stat
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from worker_wsl_auth import ACTOR_UID, AuthError, CredentialStore  # noqa: E402


def credential(refresh: str, *, expires_at: int | None = None) -> bytes:
    expiry = expires_at or int(time.time() * 1000) + 3_600_000
    return json.dumps({"claudeAiOauth": {
        "accessToken": "synthetic-access", "refreshToken": refresh,
        "subscriptionType": "max", "expiresAt": expiry,
        "refreshTokenExpiresAt": expiry + 86_400_000}}, sort_keys=True).encode()


@unittest.skipUnless(os.name == "posix" and os.geteuid() == 0,
                     "credential ownership tests require WSL root")
class CredentialStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        source_dir = root / "source"
        source_dir.mkdir(mode=0o700)
        source = source_dir / ".credentials.json"
        source.write_bytes(credential("synthetic-refresh-1"))
        source.chmod(0o600)
        self.store = CredentialStore(root / "auth", source)
        self.name = "inv-" + "a" * 32

    def test_provision_begin_refresh_finish(self) -> None:
        self.store.provision()
        self.store.inspect()
        session = self.store.begin(self.name)
        secret = session / ".credentials.json"
        self.assertEqual(ACTOR_UID, secret.stat().st_uid)
        self.assertEqual(0o600, stat.S_IMODE(secret.stat().st_mode))
        self.assertEqual(0o700, stat.S_IMODE(session.stat().st_mode))
        secret.write_bytes(credential("synthetic-refresh-2"))
        self.store.finish(self.name)
        self.store.inspect()
        self.assertEqual("synthetic-refresh-2", json.loads(
            self.store.master.read_bytes())["claudeAiOauth"]["refreshToken"])
        self.assertEqual([], list(self.store.sessions.iterdir()))

    def test_unresolved_invocation_blocks_new_work(self) -> None:
        self.store.provision()
        self.store.begin(self.name)
        with self.assertRaisesRegex(AuthError, "unreconciled"):
            self.store.begin("inv-" + "b" * 32)
        with self.assertRaisesRegex(AuthError, "unreconciled"):
            self.store.provision()

    def test_ancillary_config_is_cleaned_after_commit(self) -> None:
        self.store.provision()
        session = self.store.begin(self.name)
        (session / "backups").mkdir()
        (session / "backups" / "metadata").write_text("synthetic", encoding="utf-8")
        self.store.finish(self.name)
        self.assertFalse(session.exists())

    def test_symlink_credential_blocks_commit(self) -> None:
        self.store.provision()
        session = self.store.begin(self.name)
        secret = session / ".credentials.json"
        secret.unlink()
        secret.symlink_to(self.store.master)
        with self.assertRaisesRegex(AuthError, "private regular file"):
            self.store.finish(self.name)
        self.assertTrue(session.exists())

    def test_master_change_blocks_rollback(self) -> None:
        self.store.provision()
        session = self.store.begin(self.name)
        self.store.master.write_bytes(credential("external-refresh"))
        with self.assertRaisesRegex(AuthError, "master changed"):
            self.store.finish(self.name)
        self.assertTrue(session.exists())

    def test_discard_empty_failed_copy_preserves_master(self) -> None:
        self.store.provision()
        original = self.store.master.read_bytes()
        session = self.store.begin(self.name)
        payload = json.loads((session / ".credentials.json").read_bytes())
        payload["claudeAiOauth"]["accessToken"] = ""
        payload["claudeAiOauth"]["refreshToken"] = ""
        (session / ".credentials.json").write_text(json.dumps(payload), encoding="utf-8")
        self.store.discard_empty(self.name)
        self.store.inspect()
        self.assertEqual(original, self.store.master.read_bytes())

    def test_discard_refuses_usable_or_partial_credentials(self) -> None:
        self.store.provision()
        session = self.store.begin(self.name)
        with self.assertRaisesRegex(AuthError, "still contains a token"):
            self.store.discard_empty(self.name)
        payload = json.loads((session / ".credentials.json").read_bytes())
        payload["claudeAiOauth"]["accessToken"] = ""
        (session / ".credentials.json").write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(AuthError, "still contains a token"):
            self.store.discard_empty(self.name)
        self.assertTrue(session.exists())

    def test_expired_access_blocks_new_actor(self) -> None:
        self.store.provision()
        self.store.master.write_bytes(credential("synthetic-refresh-1",
                                                expires_at=int(time.time() * 1000) - 1))
        with self.assertRaisesRegex(AuthError, "expiresAt"):
            self.store.begin(self.name)

    def test_sync_promotes_fresh_reauthentication(self) -> None:
        self.store.provision()
        future = int(time.time() * 1000) + 7_200_000
        updated = credential("synthetic-refresh-2", expires_at=future)
        self.store.source.write_bytes(updated)
        self.store.sync()
        self.store.inspect()
        self.assertEqual(updated, self.store.master.read_bytes())

    def test_sync_refuses_older_login_and_pending_session(self) -> None:
        self.store.provision()
        future = int(time.time() * 1000) + 7_200_000
        newer = credential("synthetic-refresh-2", expires_at=future)
        self.store.master.write_bytes(newer)
        with self.assertRaisesRegex(AuthError, "older"):
            self.store.sync()
        self.assertEqual(newer, self.store.master.read_bytes())
        self.store.source.write_bytes(credential("synthetic-refresh-3",
                                                 expires_at=future + 3_600_000))
        self.store.begin(self.name)
        with self.assertRaisesRegex(AuthError, "unreconciled"):
            self.store.sync()

    def test_symlink_source_is_rejected(self) -> None:
        source = self.store.source
        replacement = source.with_name("real.json")
        source.rename(replacement)
        source.symlink_to(replacement)
        with self.assertRaisesRegex(AuthError, "private regular file"):
            self.store.provision()


if __name__ == "__main__":
    unittest.main()
