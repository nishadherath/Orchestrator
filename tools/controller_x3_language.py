#!/usr/bin/env python3
"""Frozen, task-specific prose criteria for X3 reports.

Reference reports retain their canonical slugs for stable historical controls.
Real actors may use ordinary language instead. Each tuple is an AND of concept
groups; alternatives within a group are ORs. These checks are deliberately
conservative and are coupled to verified causal probes in the protected scorer.
They are not a general semantic judge; X3 exit must calibrate wording variants.
"""
from __future__ import annotations

import re

LANGUAGE = {
    "N04-R2": {
        "mechanism": (("stale",), ("generated",), ("fixture",),
                      ("pair", "both"), ("source",)),
        "complete": (("rebuild", "regenerate"), ("both",),
                     ("fixture",), ("check", "verify", "test"),
                     ("reproducib",)),
        "partial": (("regenerate", "rebuild"), ("worker",),
                    ("fixture",), ("recheck", "verify", "test"),
                    ("pair", "both")),
    },
    "N04-R1": {
        "mechanism": (("feature",), ("disable",), ("audit",),
                      ("omitt", "miss")),
        "complete": (("verify", "test", "check"), ("flag",),
                     ("audit",), ("idempoten", "repeat")),
        "partial": (("append", "add"), ("audit",),
                    ("event",), ("recheck", "verify", "test"),
                    ("idempoten", "repeat")),
    },
    "N03-R2": {
        "mechanism": (("approved",), ("destructive",),
                      ("cutover",), ("time",), ("absent", "missing")),
        "complete": (("await", "ask", "wait"), ("approved",),
                     ("utc",), ("cutover",), ("time",)),
    },
    "N03-R1": {
        "mechanism": (("minimum",), ("client",), ("version",),
                      ("mandatory", "require"), ("trace",), ("absent", "missing")),
        "complete": (("await", "ask", "wait"), ("minimum",),
                     ("version",), ("legacy", "older"), ("client",),
                     ("decision", "approval")),
    },
    "N02-R2": {
        "mechanism": (("mutable",), ("default",), ("list",),
                      ("independent",), ("call",)),
        "complete": (("replay", "test", "verify"), ("independent",),
                     ("heading",), ("footer",), ("call",)),
        "partial": (("remove", "fix", "replace"), ("footer",),
                    ("shared", "mutable"), ("default",),
                    ("recheck", "verify", "test")),
    },
    "N02-R1": {
        "mechanism": (("strict",), ("threshold",), ("exclud", "miss"),
                      ("boundar", "equal")),
        "complete": (("recheck", "test", "verify"), ("boundar", "equal"),
                     ("adjacent", "neighbour", "neighbor"), ("value",)),
        "partial": (("tighten", "fix", "correct"),
                    ("adjacent", "neighbour", "neighbor"), ("value",),
                    ("without", "preserv"), ("boundar", "equal")),
    },
    "N01-R2": {
        "mechanism": (("stale",), ("generated",), ("header",),
                      ("hardcoded", "hard coded"), ("generator",)),
        "complete": (("regenerate", "render"), ("header",),
                     ("verify", "test", "check"), ("schema",),
                     ("variation", "change")),
        "partial": (("replace", "fix"), ("hardcoded", "hard coded"),
                    ("generator",), ("recheck", "verify", "test"),
                    ("header",)),
    },
    "N01-R1": {
        "mechanism": (("stale", "old", "legacy"), ("package",),
                      ("import",), ("path",)),
        "complete": (("exercise", "test", "verify"), ("api",),
                     ("batch",), ("export",)),
        "partial": (("migrate", "update", "move"), ("batch",),
                    ("import",), ("remove", "retire"), ("legacy", "old"),
                    ("export",)),
    },
    "C08-R2": {
        "mechanism": (("same",), ("term",), ("dual", "two"),
                      ("writer",), ("expired", "expiry"), ("unfenc", "fenc")),
        "complete": (("replay", "test", "verify"), ("overlap",),
                     ("post", "after"), ("expir",), ("takeover",)),
        "partial": (("verify", "check", "test"), ("post", "after"),
                    ("expir",), ("takeover",)),
    },
    "C08-R1": {
        "mechanism": (("unbounded", "unlimited"), ("replay",),
                      ("buffer",), ("arrival", "out of order")),
        "complete": (("replay", "test", "verify"),
                     ("capacity", "bound"), ("gap",),
                     ("order", "drain")),
        "partial": (("verify", "check", "test"),
                    ("buffer", "pending"), ("drain", "release"),
                    ("gap",)),
    },
    "C07-R2": {
        "mechanism": (("transport",), ("sequence",),
                      ("watermark",), ("state", "revision")),
        "complete": (("replay", "test", "verify"),
                     ("stale",), ("high",), ("later", "next"),
                     ("valid", "newer"), ("revision", "state")),
        "partial": (("verify", "check", "test"),
                    ("later", "next"), ("valid", "newer"),
                    ("revision", "state"), ("stale",),
                    ("watermark", "sequence")),
    },
    "C07-R1": {
        "mechanism": (("unicode", "utf"), ("character", "code point"),
                      ("frame",), ("boundar", "follow")),
        "complete": (("replay", "test", "verify"),
                     ("unicode", "utf"), ("single", "one"),
                     ("following", "next"), ("frame", "boundar")),
        "partial": (("verify", "check", "test"),
                    ("following", "next"), ("frame", "boundar"),
                    ("decod", "read")),
    },
    "C06-R2": {
        "mechanism": (("new reader",), ("old row", "historical"),
                      ("new writer",), ("legacy", "dual writ")),
        "complete": (("replay", "test", "verify"),
                     ("old row", "historical"),
                     ("old reader", "legacy reader"),
                     ("new writ", "new row")),
        "partial": (("verify", "check", "test"),
                    ("old reader", "legacy reader"),
                    ("new writ", "new row")),
    },
    "C06-R1": {
        "mechanism": (("broad", "all", "unrelated"), ("cache",),
                      ("evict", "invalidat"), ("refill", "load")),
        "complete": (("replay", "test", "verify"),
                     ("unaffected", "unchanged"),
                     ("burst", "wave"), ("refill", "load")),
        "partial": (("verify", "check", "test"),
                    ("hot key", "hot-key"), ("refill", "load"),
                    ("coalesc", "dedup", "stagger")),
    },
    "C05-R2": {
        "mechanism": (("little endian", "byte order"),
                      ("big endian", "published"),
                      ("frame", "length"), ("legacy", "old reader")),
        "complete": (("replay", "test", "verify"), ("legacy", "old"),
                     ("current", "new"), ("empty", "zero length")),
        "partial": (("verify", "check", "test"),
                    ("current", "new"), ("decod", "reader"),
                    ("empty", "zero length")),
    },
    "C05-R1": {
        "mechanism": (("queue", "pending"), ("depth", "length"),
                      ("batch",), ("size", "bound", "limit")),
        "complete": (("replay", "test", "verify"), ("burst", "full"),
                     ("drain", "consume")),
        "partial": (("verify", "check", "test"),
                    ("configur", "requested"), ("capacity", "limit"),
                    ("three", "3")),
    },
    "C04-R2": {
        "mechanism": (("pool", "connection"), ("tenant",),
                      ("session", "state"), ("return", "reset", "clear")),
        "complete": (("replay", "test", "verify"),
                     ("cross tenant", "tenant change", "tenant reuse"),
                     ("error", "exception"), ("recovery", "reuse")),
        "partial": (("verify", "check", "test"),
                    ("connection", "pool"), ("recovery", "reuse"),
                    ("error", "exception")),
    },
    "C04-R1": {
        "mechanism": (("object", "id"), ("tenant", "owner"),
                      ("lookup", "read", "access")),
        "complete": (("replay", "test", "verify"), ("foreign", "other tenant"),
                     ("archived",), ("owner", "own tenant")),
        "partial": (("verify", "check", "test"), ("owner", "own tenant"),
                    ("archived",), ("lookup", "read", "access")),
    },
    "C03-R2": {
        "mechanism": (("sequence", "watermark"),
                      ("delivery", "receipt", "webhook"),
                      ("identit", "id", "dedup")),
        "complete": (("replay", "test", "verify"),
                     ("resequence", "duplicat", "replay"),
                     ("out of order", "late", "lower sequence")),
        "partial": (("verify", "check", "test"),
                    ("lower sequence", "out of order", "late"),
                    ("distinct", "new", "different")),
    },
    "C03-R1": {
        "mechanism": (("lease",), ("owner", "worker"),
                      ("transfer", "takeover"), ("fenc", "stale", "old token")),
        "complete": (("replay", "test", "verify"),
                     ("overlap",), ("transfer", "takeover")),
        "partial": (("verify", "check", "test"),
                    ("new owner", "new worker"), ("complet", "commit")),
    },
    "C02-R2": {
        "mechanism": (("checkpoint",), ("overlap", "duplicat", "twice"),
                      ("tombstone", "delet"), ("resurrect", "ignore", "drop")),
        "complete": (("replay", "test", "verify"),
                     ("checkpoint",), ("tombstone", "delet")),
        "partial": (("verify", "check", "test"),
                    ("prefix", "checkpoint"), ("tombstone", "delet")),
    },
    "C02-R1": {
        "mechanism": (("shadow",), ("write",),
                      ("rollback", "legacy", "stale")),
        "complete": (("replay", "test", "verify"),
                     ("cutover",), ("rollback", "legacy")),
        "partial": (("verify", "check", "test"),
                    ("cutover",), ("rollback", "legacy")),
    },
    "C01-R2": {
        "mechanism": (("index",), ("stale", "lag"),
                      ("row", "authoritative", "revision")),
        "complete": (("replay", "test", "verify"),
                     ("update", "row"), ("tombstone", "delet")),
        "partial": (("verify", "check", "test"),
                    ("tombstone", "delet")),
    },
    "C01-R1": {
        "mechanism": (("sequence",), ("dedup", "replay"),
                      ("feed", "scope", "broad")),
        "complete": (("replay", "test", "verify"),
                     ("feed",), ("epoch",)),
        "partial": (("verify", "check", "test"),
                    ("epoch",), ("sequence", "replay")),
    },
    "C05-D2": {
        "mechanism": (("index",), ("page", "select"),
                      ("unbounded", "whole", "full", "overfetch")),
        "complete": (("measure", "test", "verify"),
                     ("offset",), ("narrow", "page")),
        "partial": (("verify", "check", "measure"),
                    ("narrow",), ("read", "fetch", "bound")),
    },
    "C06-D2": {
        "mechanism": (("retr",), ("storm", "burst"),
                      ("pool", "slot", "starv")),
        "complete": (("replay", "test", "verify"),
                     ("retr",), ("foreground",)),
        "partial": (("verify", "check", "test"),
                    ("retr",), ("foreground",)),
    },
    "C07-D2": {
        "mechanism": (("utc",), ("date", "day"),
                      ("sydney", "timezone", "window")),
        "complete": (("replay", "test", "verify"),
                     ("winter",), ("daylight", "summer")),
        "partial": (("verify", "check", "test"),
                    ("daylight", "summer", "offset")),
    },
    "C08-D2": {
        "mechanism": (("api",), ("contract", "compatib"),
                      ("immutab", "conflict", "version")),
        "complete": (("ask", "await", "request"),
                     ("owner",), ("compatib", "version")),
    },
    "C04-D2": {
        "mechanism": (("retr", "attempt"), ("context",),
                      ("drop", "loss", "missing")),
        "complete": (("replay", "test", "verify"),
                     ("tenant",), ("trace",)),
        "partial": (("verify", "check", "test"),
                    ("trace",), ("retr", "attempt")),
    },
    "C02-D2": {
        "mechanism": (("envelope",), ("drop", "loss", "discard"),
                      ("field", "metadata", "extension")),
        "complete": (("replay", "test", "verify"),
                     ("unknown", "extension", "metadata")),
        "partial": (("verify", "check", "test"),
                    ("unknown", "extension")),
    },
    "C01-D2": {
        "mechanism": (("cache",), ("namespace", "composite"),
                      ("alias", "collid", "boundar", "concat")),
        "complete": (("replay", "test", "verify"),
                     ("punctuation", "delimiter", "alias")),
        "partial": (("verify", "check", "test"),
                    ("punctuation", "delimiter", "framing")),
    },
    "N04-D2": {
        "mechanism": (("rotat", "key"), ("blue", "old", "staged"),
                      ("only", "incomplete", "missing", "not")),
        "complete": (("test", "verify", "check"), ("sign",),
                     ("dual", "both", "overlap")),
        "partial": (("switch", "change", "move"), ("sign",),
                    ("green", "new")),
    },
    "C01-D1": {
        "mechanism": (("order", "identifier", "id"), ("alias", "normalis", "normaliz", "version")),
        "complete": (("replay", "test", "verify"), ("cross account", "alias", "receipt")),
        "partial": (("verify", "check", "test"), ("prefix", "collision")),
    },
    "C02-D1": {
        "mechanism": (("migration", "backfill", "dual read"), ("precedence", "overwrite", "newer", "current")),
        "complete": (("replay", "test", "verify"), ("mixed version", "cutover", "legacy")),
        "partial": (("verify", "check", "test"), ("zero", "current")),
    },
    "C03-D1": {
        "mechanism": (("retr", "replay"), ("idempoten", "receipt", "duplicate")),
        "complete": (("replay", "test", "verify"), ("cutover", "retry", "payment")),
        "partial": (("verify", "check", "test"), ("conflict", "payload")),
    },
    "C03-D2": {
        "mechanism": (("outbox", "delivery"), ("lease", "fenc", "stale")),
        "complete": (("replay", "test", "verify"), ("lease", "expiry", "expiration")),
        "partial": (("verify", "check", "test"), ("duplicate", "ack")),
    },
    "C04-D1": {
        "mechanism": (("tenant",), ("cache",), ("key", "namespace", "scope")),
        "complete": (("replay", "test", "verify"), ("tenant", "cache")),
        "partial": (("verify", "check", "test"), ("update", "same tenant")),
    },
    "C05-D1": {
        "mechanism": (("join",), ("unbounded", "cartesian", "memory", "state")),
        "complete": (("replay", "test", "measure"), ("sparse", "stream", "cap")),
        "partial": (("verify", "check", "measure"), ("bound", "state", "memory")),
    },
    "C06-D1": {
        "mechanism": (("worker", "clock"), ("lease", "expiry", "expiration")),
        "complete": (("compare", "measure", "verify"), ("server", "time", "clock")),
        "partial": (("verify", "check", "test"), ("expiry", "expiration")),
    },
    "C07-D1": {
        "mechanism": (("round", "decimal", "cent"), ("ledger", "statement", "consumer")),
        "complete": (("reconcile", "verify", "test"), ("ledger", "statement", "delta")),
        "partial": (("verify", "check", "test"), ("negative", "refund")),
    },
    "C08-D1": {
        "mechanism": (("lock",), ("order",), ("conflict", "incompatib", "oppos")),
        "complete": (("await", "ask", "request", "clarify"), ("owner", "operator", "decision"), ("lock", "order")),
    },
    "N01-D1": {
        "mechanism": (("import", "symbol", "format cents"), ("stale", "old", "rename", "updated")),
        "complete": (("run", "verify", "test"), ("import", "negative")),
        "partial": (("remove", "update", "rename"), ("legacy", "old", "import")),
    },
    "N01-D2": {
        "mechanism": (("timeout", "deadline"), ("key", "unit", "millisecond", "second")),
        "complete": (("replay", "verify", "test"), ("override", "new key")),
        "partial": (("remove", "update", "rename"), ("legacy", "old", "reader")),
    },
    "N02-D1": {
        "mechanism": (("slice", "bound", "limit"), ("inclusive", "extra", "one")),
        "complete": (("run", "verify", "test"), ("bound", "limit")),
        "partial": (("check", "verify", "test"), ("interior", "bound")),
    },
    "N02-D2": {
        "mechanism": (("profile",), ("null", "missing", "absent", "derefer")),
        "complete": (("run", "verify", "test"), ("null", "missing")),
        "partial": (("guard", "check", "handle"), ("missing", "email")),
    },
    "N03-D1": {
        "mechanism": (("retention",), ("duration", "days"), ("missing", "absent", "unknown", "unapproved")),
        "complete": (("wait", "ask", "request"), ("operator", "approval"), ("retention", "days")),
    },
    "N03-D2": {
        "mechanism": (("region",), ("pilot",), ("missing", "absent", "unknown", "unapproved")),
        "complete": (("wait", "ask", "request"), ("approved", "operator"), ("region",)),
    },
    "N04-D1": {
        "mechanism": (("manifest", "pin"), ("drift", "stale", "mismatch", "old")),
        "complete": (("verify", "check", "compare"), ("both", "audit", "release"), ("pin", "manifest")),
        "partial": (("update", "fix", "change"), ("audit",), ("pin",)),
    },
}

DENIALS = (
    r"\bno (?:known )?(?:bug|defect|issue|problem|regression)\b",
    r"\balready (?:correct|working)\b",
    r"\bnothing (?:is )?wrong\b",
    r"\bnot (?:the|a) (?:cause|problem|issue)\b",
    r"\bcannot reproduce\b",
)


def matches(task_id: str, field: str, value: str, canonical: str) -> bool:
    """Accept the canonical control value or a bounded equivalent description."""
    if not isinstance(value, str) or not value.strip() or len(value) > 500:
        return False
    if value == canonical:
        return True
    groups = LANGUAGE[task_id].get(field)
    if groups is None:
        return False
    normal = " ".join(re.findall(r"[a-z0-9]+", value.lower()))
    if field == "mechanism" and any(re.search(pattern, normal)
                                     for pattern in DENIALS):
        return False
    return all(any(term in normal for term in alternatives)
               for alternatives in groups)
