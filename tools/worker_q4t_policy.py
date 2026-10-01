#!/usr/bin/env python3
"""Prospective Q4T stop policy for settled report failures.

The frozen Q4S runner stops on invalid structured transport. A successor
screen may use this policy only after its own manifest and approval are bound;
it never rewrites Q4S evidence or turns a missing report into acceptance.
"""
from __future__ import annotations

import math


def settled_stop_reason(episode: dict, *, episode_maximum_usd: float,
                        candidate_positive: bool) -> str | None:
    """Return a safety stop, or None when a report failure can be scored.

    The caller must first validate source, binding, journal and grade digests.
    This function is deliberately conservative about accounting and identity,
    but a stopped, charged report failure is measurement data, not uncertainty.
    """
    if (not isinstance(episode, dict)
            or type(candidate_positive) is not bool
            or type(episode_maximum_usd) not in (int, float)
            or not math.isfinite(episode_maximum_usd)
            or episode_maximum_usd <= 0):
        raise ValueError("Q4T stop policy inputs are invalid")
    settlement = episode.get("settlement") or {}
    attempts = episode.get("attempts") or []
    amount = settlement.get("charged_usd")
    if (not isinstance(attempts, list) or not attempts
            or settlement.get("cost_settled") is not True
            or settlement.get("writer_stopped") is not True
            or settlement.get("provider_calls") != len(attempts)
            or type(amount) not in (int, float) or not math.isfinite(amount)
            or amount < 0):
        return "unsettled episode accounting"
    if amount > episode_maximum_usd:
        return "settled episode allocation overrun"
    if episode.get("protected_integrity") is not True:
        return "protected source integrity unverified"
    for attempt in attempts:
        cost = attempt.get("cost_usd")
        if (attempt.get("terminal") is not True
                or attempt.get("writer_stopped") is not True
                or type(cost) not in (int, float) or not math.isfinite(cost)
                or cost < 0):
            return "unsettled attempt accounting"
        if attempt.get("identity_valid") is not True:
            return "settled model identity mismatch"
    if not math.isclose(sum(item["cost_usd"] for item in attempts), amount,
                        abs_tol=1e-8):
        return "settled attempt charges disagree"
    quality = episode.get("quality_v2") or {}
    if quality.get("report_observability") != "present" and quality.get(
            "hidden_accepted") is not False:
        return "invalid grade for missing report"
    if candidate_positive and quality.get("critical_error") is True:
        return "candidate critical error"
    known_report_failure = False
    if episode.get("root_state") == "blocked":
        last = attempts[-1]
        report = last.get("evaluation_report") or {}
        transport = last.get("evaluation_transport") or {}
        diagnostics = last.get("q4t_diagnostics") or {}
        known_report_failure = (
            episode.get("qualification_eligible") is False
            and report.get("observability") == "transport-invalid"
            and quality.get("report_observability") == "transport-invalid"
            and transport.get("mode") == "claude-code-json-schema-v2"
            and transport.get("structured_retry_limit") == 5
            and transport.get("structured_output_present") is False
            and diagnostics.get("result_subtype") in {
                "error_max_structured_output_retries", "success"}
            and diagnostics.get("invalid_line_count") == 0
            and diagnostics.get("returncode") in {0, 1})
        if not known_report_failure:
            return "blocked root without a proven report transport failure"
    if quality.get("inconclusive") is True and not known_report_failure:
        return "inconclusive episode grade"
    if quality.get("report_observability") != "present" and not known_report_failure:
        return "missing report without a proven report transport failure"
    # A missing report earns no diagnosis/report credit and no hidden
    # acceptance under quality-v2. The caller retains its original grade.
    return None
