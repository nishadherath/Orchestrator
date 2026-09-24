#!/usr/bin/env python3
"""Evaluator-only reference semantics for the N4 synthetic consumer corpus.

Never copy this module into an actor workspace or expose it through actor Graft.
The corpus generator materialises data-only expected outputs from these pure
functions. None of these functions execute candidate code.
"""
from __future__ import annotations

import hashlib
import hmac
import posixpath
from decimal import Decimal, ROUND_HALF_EVEN


def expected(task_id: str, data: dict) -> object:
    """Compute one independently specified JSON result for a public input."""
    if task_id == "D01":
        for layer in ("cli", "environment", "file", "default"):
            if data.get(layer) is not None:
                return {"value": data[layer], "source": layer}
        return {"value": None, "source": None}
    if task_id == "D02":
        raw = data.get("port")
        if isinstance(raw, bool) or not isinstance(raw, (int, str)):
            return {"ok": False, "error": "invalid-port"}
        try:
            port = int(raw)
        except ValueError:
            return {"ok": False, "error": "invalid-port"}
        return ({"ok": True, "port": port} if 1 <= port <= 65535
                else {"ok": False, "error": "invalid-port"})
    if task_id == "R01":
        current = data["initial"]
        reads = []
        for event in data["events"]:
            if event["kind"] == "reload":
                current = event["secret"]
            else:
                reads.append(current)
        return {"reads": reads, "current": current}
    if task_id == "R02":
        name = data["requested"]
        if name.startswith("/") or ".." in name.split("/"):
            return {"ok": False, "error": "outside-root"}
        return {"ok": True, "path": posixpath.normpath(data["root"].rstrip("/") + "/" + name)}
    if task_id == "D03":
        seen = []
        retryable = data["method"] in {"GET", "PUT", "DELETE"}
        for status in data["statuses"][:data["max_attempts"]]:
            seen.append(status)
            if status != 503 or not retryable:
                break
        return {"attempts": seen, "final": seen[-1] if seen else None}
    if task_id == "D04":
        elapsed = done = 0
        for hop in data["hops_ms"]:
            if elapsed + hop > data["budget_ms"]:
                return {"completed_hops": done, "elapsed_ms": elapsed,
                        "timed_out": True}
            elapsed += hop
            done += 1
        return {"completed_hops": done, "elapsed_ms": elapsed,
                "timed_out": False}
    if task_id == "R03":
        failures = ticks = 0
        state = "closed"
        admitted = []
        for event in data["events"]:
            if event == "tick":
                if state == "open":
                    ticks += 1
                    if ticks >= data["reset_ticks"]:
                        state = "half-open"
                continue
            can_call = state != "open"
            admitted.append(can_call)
            if not can_call:
                continue
            if event == "ok":
                state, failures, ticks = "closed", 0, 0
            else:
                failures += 1
                if state == "half-open" or failures >= data["threshold"]:
                    state, ticks = "open", 0
        return {"admitted": admitted, "state": state}
    if task_id == "R04":
        active: list[str] = []
        waiting: list[str] = []
        cancelled: list[str] = []
        for event in data["events"]:
            kind, ident = event["kind"], event["id"]
            if kind == "acquire":
                (active if len(active) < data["capacity"] else waiting).append(ident)
            else:
                if ident in active:
                    active.remove(ident)
                elif ident in waiting:
                    waiting.remove(ident)
                if kind == "cancel":
                    cancelled.append(ident)
                while waiting and len(active) < data["capacity"]:
                    active.append(waiting.pop(0))
        return {"active": active, "waiting": waiting,
                "cancelled": cancelled}
    if task_id == "D05":
        ids = [row["id"] for row in data["rows"]]
        if len(ids) != len(set(ids)):
            return {"committed": [], "error": "duplicate-id"}
        if any(row["amount"] < 0 for row in data["rows"]):
            return {"committed": [], "error": "negative-amount"}
        return {"committed": ids, "error": None}
    if task_id == "D06":
        missing = [step for step in data["required"] if step not in data["applied"]]
        return {"apply": missing, "complete": not missing}
    if task_id == "R05":
        unique = {}
        for row in data["records"]:
            if row["seq"] > data["checkpoint"] and row["seq"] not in unique:
                unique[row["seq"]] = row["value"]
        ordered = sorted(unique)
        return {"values": [unique[n] for n in ordered],
                "checkpoint": max([data["checkpoint"], *ordered])}
    if task_id == "R06":
        balance = Decimal(data["start"])
        for entry in data["entries"]:
            balance += Decimal(entry)
        balance = balance.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
        return ({"ok": False, "error": "overdraft"} if balance < 0
                else {"ok": True, "balance": f"{balance:.2f}"})
    if task_id == "D07":
        cache = {}
        reads = []
        for row in data["operations"]:
            key = (row["tenant"], row["key"])
            if row["kind"] == "put":
                cache[key] = row["value"]
            else:
                reads.append(cache.get(key))
        return {"reads": reads}
    if task_id == "D08":
        outcomes = {}
        results = []
        for row in data["requests"]:
            if row["key"] not in outcomes:
                outcomes[row["key"]] = row["outcome"]
            results.append(outcomes[row["key"]])
        return {"executions": len(outcomes), "results": results}
    if task_id == "R07":
        newest = {}
        for row in data["completions"]:
            old = newest.get(row["key"])
            if old is None or row["version"] > old["version"]:
                newest[row["key"]] = {"version": row["version"], "value": row["value"]}
        return {"cache": newest}
    if task_id == "R08":
        # Fixed-width workers take tasks in input order. Shutdown rejects only
        # work not yet started; accepted work may finish within the deadline.
        slots = [0] * data["capacity"]
        completed = []
        rejected = []
        for task in data["tasks"]:
            slot = min(range(len(slots)), key=slots.__getitem__)
            start = slots[slot]
            if start >= data["shutdown_at"]:
                rejected.append(task["id"])
                continue
            finish = start + task["duration"]
            slots[slot] = finish
            if finish <= data["drain_deadline"]:
                completed.append(task["id"])
        return {"completed": completed, "rejected": rejected}
    if task_id == "D09":
        etag = data["etag"]
        if data.get("if_none_match") == etag:
            return {"status": 304, "body": None, "etag": etag}
        return {"status": 200, "body": data["body"], "etag": etag}
    if task_id == "D10":
        signature = hmac.new(data["key"].encode(), data["body"].encode(),
                             hashlib.sha256).hexdigest()
        return {"valid": hmac.compare_digest(signature, data["signature"])}
    if task_id == "R09":
        remaining = sorted((row for row in data["records"]
                            if data["cursor"] is None or row["id"] > data["cursor"]),
                           key=lambda row: row["id"])
        page = remaining[:data["limit"]]
        return {"ids": [row["id"] for row in page],
                "next_cursor": page[-1]["id"] if len(remaining) > len(page) and page else None}
    if task_id == "R10":
        buffer = bytes.fromhex("".join(data["chunks_hex"]))
        frames = []
        while len(buffer) >= 2:
            size = int.from_bytes(buffer[:2], "big")
            if len(buffer) < 2 + size:
                break
            try:
                frames.append(buffer[2:2 + size].decode("utf-8"))
            except UnicodeDecodeError:
                return {"error": "invalid-utf8"}
            buffer = buffer[2 + size:]
        return {"frames": frames, "remainder_hex": buffer.hex()}
    if task_id == "D11":
        totals = {row["stage"]: row["count"] * row["ms_each"]
                  for row in data["measurements"]}
        winner = max(totals, key=totals.__getitem__)
        return {"bottleneck": winner,
                "rejected_premise": winner != data["named_hotspot"]}
    if task_id == "D12":
        days = data.get("retention_days")
        if days is None:
            return {"action": "clarify", "missing": "retention_days"}
        return {"action": "delete", "ids": [row["id"] for row in data["records"]
                                             if row["age_days"] > days]}
    if task_id == "R11":
        if data["actual_upstream"] != data["expected_upstream"]:
            return {"action": "no-code-change", "cause": "upstream-config",
                    "observed": data["actual_upstream"]}
        return {"action": "investigate-code", "cause": "undetermined",
                "observed": data["actual_upstream"]}
    if task_id == "R12":
        passed = sum(bool(item) for item in data["local_checks"])
        if data.get("external_key") is None:
            return {"status": "partial", "local_passed": passed,
                    "blocked_on": "external_key"}
        return {"status": "complete" if passed == len(data["local_checks"]) else "partial",
                "local_passed": passed, "blocked_on": None}
    raise ValueError(f"unknown evaluator task: {task_id}")
