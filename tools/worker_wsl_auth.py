#!/usr/bin/env python3
"""Root-owned Claude.ai credential handoff for one isolated WSL invocation.

Only the root launcher calls this module. Each invocation receives a private
copy under a root-only parent; the namespace binds that copy outside the
actor's working directory. A stopped invocation commits Claude Code's refreshed
credential atomically. An interrupted invocation remains on disk and blocks
the next one until an operator reconciles it, so refresh-token rotation cannot
be silently rolled back.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import time
from pathlib import Path

BASE = Path("/var/lib/orchestrator-worker-n4/auth")
SOURCE = Path("/home/wsl/.claude/.credentials.json")
ACTOR_UID = 65534
NAME = re.compile(r"inv-[0-9a-f]{32}\Z")
MAX_BYTES = 16_384


class AuthError(RuntimeError):
    """A credential state or ownership invariant failed."""


def _credential(path: Path, owner: int) -> bytes:
    info = path.lstat()
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != owner
            or stat.S_IMODE(info.st_mode) != 0o600 or info.st_size > MAX_BYTES):
        raise AuthError("credential is not a private regular file")
    data = path.read_bytes()
    try:
        oauth = json.loads(data)["claudeAiOauth"]
    except (ValueError, TypeError, KeyError) as exc:
        raise AuthError("Claude.ai OAuth credential structure is invalid") from exc
    if (not isinstance(oauth, dict)
            or any(not isinstance(oauth.get(key), str) or not oauth[key]
                   for key in ("accessToken", "refreshToken", "subscriptionType"))):
        raise AuthError("Claude.ai OAuth credential is incomplete")
    return data


def _fresh(data: bytes) -> None:
    """Require enough token lifetime for a bounded worker invocation.

    Claude Code can report ``loggedIn`` for an expired access token and has
    been observed erasing its private copy after a failed headless refresh.
    Reject that state before granting the copy to an actor.
    """
    oauth = json.loads(data)["claudeAiOauth"]
    minimum = int(time.time() * 1000) + 300_000
    for key in ("expiresAt", "refreshTokenExpiresAt"):
        expiry = oauth.get(key)
        if type(expiry) not in (int, float) or expiry <= minimum:
            raise AuthError(f"Claude.ai {key} is expired or too near expiry")


def _directory(path: Path, owner: int, mode: int) -> None:
    info = path.lstat()
    if (not stat.S_ISDIR(info.st_mode) or info.st_uid != owner
            or stat.S_IMODE(info.st_mode) != mode):
        raise AuthError("credential directory ownership or mode is wrong")


def _atomic_private(path: Path, data: bytes) -> None:
    temporary = path.with_name(path.name + ".new")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if temporary.exists():
            temporary.unlink()


class CredentialStore:
    """Persistent root master and one private, recoverable invocation copy."""

    def __init__(self, base: Path = BASE, source: Path = SOURCE):
        self.base = base
        self.source = source
        self.master = base / ".credentials.json"
        self.sessions = base / "sessions"

    def provision(self) -> None:
        _directory(self.source.parent, self.source.parent.stat().st_uid, 0o700)
        source = _credential(self.source, self.source.stat().st_uid)
        _fresh(source)
        self.base.mkdir(mode=0o700, exist_ok=True)
        self.sessions.mkdir(mode=0o700, exist_ok=True)
        _directory(self.base, 0, 0o700)
        _directory(self.sessions, 0, 0o700)
        if any(self.sessions.iterdir()):
            raise AuthError("unreconciled credential invocation exists")
        if self.master.exists():
            _credential(self.master, 0)
            if self.master.read_bytes() != source:
                raise AuthError("master differs from WSL login; reconcile before replacing")
            return
        _atomic_private(self.master, source)

    def sync(self) -> None:
        """Promote a freshly reauthenticated WSL login with no active actor."""
        _directory(self.source.parent, self.source.parent.stat().st_uid, 0o700)
        source = _credential(self.source, self.source.stat().st_uid)
        _fresh(source)
        _directory(self.base, 0, 0o700)
        _directory(self.sessions, 0, 0o700)
        if any(self.sessions.iterdir()):
            raise AuthError("unreconciled credential invocation exists")
        master = _credential(self.master, 0)
        old_expiry = json.loads(master)["claudeAiOauth"]["expiresAt"]
        new_expiry = json.loads(source)["claudeAiOauth"]["expiresAt"]
        if type(old_expiry) not in (int, float) or new_expiry < old_expiry:
            raise AuthError("WSL login is older than the current master")
        _atomic_private(self.master, source)

    def inspect(self) -> None:
        """Validate local handoff state without exposing credential values."""
        _directory(self.base, 0, 0o700)
        _directory(self.sessions, 0, 0o700)
        _fresh(_credential(self.master, 0))
        if any(self.sessions.iterdir()):
            raise AuthError("unreconciled credential invocation exists")

    def begin(self, name: str) -> Path:
        if not NAME.fullmatch(name):
            raise AuthError("invalid credential invocation identity")
        _directory(self.base, 0, 0o700)
        _directory(self.sessions, 0, 0o700)
        if any(self.sessions.iterdir()):
            raise AuthError("unreconciled credential invocation exists")
        data = _credential(self.master, 0)
        _fresh(data)
        session = self.sessions / name
        session.mkdir(mode=0o700)
        os.chown(session, ACTOR_UID, ACTOR_UID)
        token = session / ".credentials.json"
        descriptor = os.open(token, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            os.fchown(stream.fileno(), ACTOR_UID, ACTOR_UID)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        _atomic_private(self.sessions / (name + ".sha256"),
                        hashlib.sha256(data).hexdigest().encode("ascii"))
        return session

    def finish(self, name: str) -> None:
        if not NAME.fullmatch(name):
            raise AuthError("invalid credential invocation identity")
        _directory(self.sessions, 0, 0o700)
        session = self.sessions / name
        _directory(session, ACTOR_UID, 0o700)
        data = _credential(session / ".credentials.json", ACTOR_UID)
        recorded = self._recorded_master(name)
        _atomic_private(self.master, data)
        # Claude Code writes benign config, lock and backup files beside its
        # credential. This directory is not the actor tree and rmtree's fd-
        # based implementation does not follow symlinks out of it.
        shutil.rmtree(session)
        recorded.unlink()

    def _recorded_master(self, name: str) -> Path:
        recorded = self.sessions / (name + ".sha256")
        info = recorded.lstat()
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != 0
                or stat.S_IMODE(info.st_mode) != 0o600
                or recorded.read_text(encoding="ascii") !=
                hashlib.sha256(_credential(self.master, 0)).hexdigest()):
            raise AuthError("master changed during credential invocation")
        return recorded

    def discard_empty(self, name: str) -> None:
        """Remove a failed invocation only when Claude erased both token fields.

        A usable or partially refreshed credential must go through ``finish``
        or remain blocked for manual reconciliation. The master is untouched.
        """
        if not NAME.fullmatch(name):
            raise AuthError("invalid credential invocation identity")
        _directory(self.sessions, 0, 0o700)
        session = self.sessions / name
        _directory(session, ACTOR_UID, 0o700)
        token = session / ".credentials.json"
        info = token.lstat()
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != ACTOR_UID
                or stat.S_IMODE(info.st_mode) != 0o600
                or info.st_size > MAX_BYTES):
            raise AuthError("credential is not a private regular file")
        try:
            oauth = json.loads(token.read_bytes())["claudeAiOauth"]
        except (ValueError, TypeError, KeyError) as exc:
            raise AuthError("failed invocation credential structure is invalid") from exc
        if (not isinstance(oauth, dict) or oauth.get("accessToken") != ""
                or oauth.get("refreshToken") != ""):
            raise AuthError("failed invocation still contains a token")
        recorded = self._recorded_master(name)
        shutil.rmtree(session)
        recorded.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("provision", "sync", "inspect", "begin", "finish",
                                           "discard-empty"))
    parser.add_argument("name", nargs="?")
    args = parser.parse_args()
    if os.geteuid() != 0:
        parser.error("root identity required")
    store = CredentialStore()
    try:
        if args.action == "provision":
            if args.name is not None:
                parser.error("provision takes no invocation name")
            store.provision()
        elif args.action == "sync":
            if args.name is not None:
                parser.error("sync takes no invocation name")
            store.sync()
        elif args.action == "inspect":
            if args.name is not None:
                parser.error("inspect takes no invocation name")
            store.inspect()
        elif args.action == "begin":
            if args.name is None:
                parser.error("begin requires an invocation name")
            store.begin(args.name)
        elif args.action == "finish":
            if args.name is None:
                parser.error("finish requires an invocation name")
            store.finish(args.name)
        else:
            if args.name is None:
                parser.error("discard-empty requires an invocation name")
            store.discard_empty(args.name)
    except (AuthError, OSError) as exc:
        print(f"subscription credential handoff blocked: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
