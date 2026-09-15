#!/usr/bin/env python3
"""Generate src/routing_priors.json from the benchmark confirmations on record.

    python3 tools/generate_priors.py            regenerate and write, print a summary
    python3 tools/generate_priors.py --check     write nothing; exit 0 if the committed
                                                  file already matches, 1 and a diagnostic
                                                  otherwise

Responsible for: the arithmetic behind every prior in that file (docs/PLAN-2.md
Stage 1.4, D64): a Laplace mean (passes + 1) / (n + 2) over the confirmed
counts docs/FRONTIERS.md cites, an effective sample size capped at 10 for a
measured bucket, 4 for one bracketed between measured neighbours, and 3 for
a policy value inherited across blast radius, so a consumer project's own
ledger can move a bucket after a handful of its own outcomes.

Deliberately does not: read the result files itself. The counts are typed
here from FRONTIERS.md's confirmations, which are the reviewed record; the
provenance string on every entry names them. Re-run after changing a count
and commit the regenerated file; check.py's ROUTE-PRIORS check (Stage 2.5)
runs this with --check so verifying the committed file matches never has
the side effect of rewriting it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CAP = 10
PRIORS_PATH = REPO / "src" / "routing_priors.json"


def _beta(passes, n, cap=CAP, kind="measured", prov=""):
    m = (passes + 1) / (n + 2)
    n_eff = min(n, cap)
    return {"alpha": round(m * n_eff, 3), "beta": round((1 - m) * n_eff, 3), "mean": round(m, 3),
            "n_measured": n, "passes_measured": passes, "n_eff": n_eff, "kind": kind, "provenance": prov}


def build_priors() -> dict:
    """Pure: returns the document; writes nothing. The commit that added
    this file is where the aggregation and Laplace/n_eff arithmetic were
    reasoned through; nothing here reads a result file directly."""
    F = "docs/FRONTIERS.md and the benchmark confirmations it cites: "
    buckets: dict[str, dict] = {}

    def bucket(s, h, b, floor, rungs=None):
        buckets[f"{s}/{h}/{b}"] = {"sensitivity": s, "horizon": h, "blast": b, "floor": floor,
                                    "rungs_given_failure_below": rungs or {}}

    bucket("mechanical", "short", "contained", _beta(18, 18, prov=F + "T1 confirmed 9 of 9 twice (04d2acc original and replication); fixtures F01, F02, F15"))
    bucket("mechanical", "medium", "contained", _beta(36, 36, cap=4, kind="bracketed", prov=F + "no task at this triple; T1 (short) and T2 (long) both 9 of 9 twice, D19 bracket; fixture F03; n_eff capped at 4"))
    bucket("mechanical", "long", "contained", _beta(18, 18, prov=F + "T2 confirmed 9 of 9 twice"))
    bucket("structured", "short", "contained", _beta(18, 18, prov=F + "T3 confirmed 9 of 9 twice; fixture F04"))
    bucket("structured", "medium", "contained", _beta(36, 36, cap=4, kind="bracketed", prov=F + "no task at this triple; T3 and T4 bracket; fixture F05; n_eff capped at 4"))
    bucket("structured", "long", "contained", _beta(18, 18, prov=F + "T4 confirmed 9 of 9 twice after the D16/D17 grader fix; fixture F07"))
    bucket("open", "short", "contained", _beta(27, 27, prov=F + "T5 9 of 9 twice, T8 9 of 9 after D30's regrade; fixture F09"))
    bucket("open", "medium", "contained",
           _beta(9, 12, prov=F + "T9 9 of 9 at the floor (a false measurement), T10 0 of 3 at the floor (a false constraint, D42); the triple cannot separate them, D42 calls T10 a disposition frontier; fixture F10"),
           rungs={"worker-sonnet-xhigh": _beta(0, 12, prov="T10: sonnet-xhigh 0 of 12 given floor failure (D42); the intermediate sonnet rungs are not in the default ladder for this reason"),
                  "worker-opus-high": _beta(12, 12, prov="T10: opus-high 12 of 12 given floor failure (D42, the only confirmed cell above the floor)")})
    bucket("open", "long", "contained", _beta(36, 36, prov=F + "T6 9 of 9 twice, T7 9 of 9 (after D20), T11 9 of 9; fixture F13"))

    for key in list(buckets):
        s, h, _ = key.split("/")
        src = buckets[key]["floor"]
        inh = _beta(src["passes_measured"], src["n_measured"], cap=3, kind="policy-inherited",
                    prov=f"blast radius is unmeasurable by exit code (docs/BENCHMARK-DESIGN.md); inherits {key}'s floor mean at n_eff 3 so a project's first three outcomes dominate it; a policy, not a measurement")
        rungs = {k: dict(v, kind="policy-inherited", n_eff=min(v["n_eff"], 3)) for k, v in buckets[key]["rungs_given_failure_below"].items()}
        bucket(s, h, "consequential", inh, rungs=rungs)

    for key, b in buckets.items():
        if "worker-opus-high" not in b["rungs_given_failure_below"]:
            b["rungs_given_failure_below"]["worker-opus-high"] = {
                "alpha": 2.7, "beta": 0.3, "mean": 0.9, "n_measured": 0, "passes_measured": 0, "n_eff": 3, "kind": "policy-default",
                "provenance": "no floor failure ever measured in this bucket, so no conditional data; assumes the one confirmed cell above the floor passes 0.9 of what the floor fails, weakly held"}

    return {
        "_comment": "Per-bucket priors for tools/route.py (docs/PLAN-2.md Stage 1.4, D64). A bucket is sensitivity/horizon/blast. 'floor' is a Beta prior on worker-sonnet-low passing; each rung entry is a Beta prior on that cell passing given every cheaper active rung failed (the benchmark staircase only climbed after failure, so its measured rates at higher cells are exactly that conditional). Means are Laplace ((passes+1)/(n+2)); effective sample sizes are capped (measured 10, bracketed 4, policy 3) so a consumer project's own ledger moves a bucket after a handful of its own outcomes. 'kind' says whether a number was measured, bracketed between measured neighbours, inherited across blast radius as policy, or a weakly held default. Every threshold named steering_* steers routing and may never be cited as evidence; the reporting bar is nine runs with a Wilson lower bound above 0.7 and lives in the harness, not here.",
        "version": 1,
        "generated_on": "2026-09-15",
        "generated_by": "docs/PLAN-2.md Stage 1.4; the aggregation and Laplace/n_eff arithmetic are in the commit that added this file",
        "cells": ["worker-sonnet-low", "worker-sonnet-medium", "worker-sonnet-high", "worker-sonnet-xhigh", "worker-sonnet-max",
                  "worker-opus-low", "worker-opus-medium", "worker-opus-high", "worker-opus-xhigh", "worker-opus-max",
                  "worker-fable-low", "worker-fable-medium", "worker-fable-high", "worker-fable-xhigh", "worker-fable-max"],
        "default_ladder": ["worker-sonnet-low", "worker-opus-high", "controller", "worker-opus-max"],
        "ladder_notes": "Cheapest first. The intermediate sonnet rungs are omitted on evidence (T10: sonnet-medium 1 of 3, sonnet-high 0 of 3, sonnet-xhigh 0 of 12 given floor failure, against opus-high 12 of 12; D42). 'controller' is tools/system_controller.py quick mode plus one floor instantiation (D55); it sits after the confirmed cell and before the unmeasured frontier, so the lowest capable configurations are tried first, per Jeb's brief. The falsified-constraint trigger (D63) is separate and jumps from the floor straight to the controller. A project's ledger can activate an omitted cell for a bucket (rung_activation below).",
        "steering": {
            "steering_first_rung_min_pass": 0.6,
            "steering_first_rung_note": "the first cell tried is the cheapest active rung whose posterior pass probability is at least this; if none clears it, the cheapest rung is still tried first (the floor is always the default), and the Controller rule below decides whether to pre-empt",
            "steering_rung_activation_min_pass": 0.5,
            "steering_rung_activation_min_n": 3,
            "rung_activation": "a cell not in default_ladder becomes an active rung for a bucket in a project once that project's ledger holds at least steering_rung_activation_min_n outcomes at that cell in that bucket and the posterior conditional pass probability is at least steering_rung_activation_min_pass; it is inserted in cost order (cost_table.json)",
            "ledger_overrides_after": 5,
            "ledger_overrides_note": "cost and wall-clock projections use the project's own ledger means for a cell once it has this many entries, else src/cost_table.json",
            "handoff_context_percent": 70,
            "handoff_context_note": "route.py --explain's context line recommends a handoff at this percentage of the model's context window (docs/PLAN-3.md Stage B, D68); it never blocks or replaces the platform's own auto-compact, which fires at autocompact_window_tokens",
            "context_stale_s": 600,
            "context_stale_note": "a .claude/context-usage.json sample older than this is reported as stale rather than aged, since the status line only updates on session events (docs/en/statusline); the threshold comparison against handoff_context_percent is still made on a stale sample",
            "autocompact_window_tokens": 200000,
            "autocompact_window_note": "the value dist/settings.fragment.json sets as autoCompactWindow (docs/COMPACTION-DESIGN.md section 7); handoff_context_percent must fire before this is reached on the 200K reference model ROUTE-PRIORS checks against, which is why the two are shipped together and checked together rather than independently"
        },
        "controller_rule": {
            "reactive": "after the last active cell rung fails on the same task, or on ROUTING.md section 4's falsified-constraint signal (D63), route to the controller before the frontier",
            "proactive_expected_cost": "fire before the first call when E_ladder + P_fail_all * failure_cost > controller_cost, where E_ladder is the sequential expected cost down the active rungs (cost of rung k times the probability of reaching it), P_fail_all is the posterior probability every rung fails, and controller_cost is cost_table.json controller.quick_mode_run_usd + instantiation_usd. On the priors in this file this fires in no bucket; it is the path a project's own ledger opens when a bucket keeps escalating",
            "failure_cost": {
                "contained": "E_ladder (the work is redone)",
                "consequential_usd": 10.0,
                "consequential_note": "policy, not a measurement: what a wrong answer on a committed, published or depended-on change costs its owner, set at roughly ten times a floor run. Raise it to make the Controller fire sooner on consequential work; lower it to make it fire later. Recorded as a risk-appetite dial in ROUTING.md itself (criterion 3, D38)"
            },
            "proactive_policy": {
                "enabled": True,
                "when": {"sensitivity": ["open"], "blast": ["consequential"]},
                "label": "risk-appetite policy, unmeasured: on open, consequential tasks the Controller runs first for its audit trail (premise ledger, REPORT.md), at cost_table.json's controller cost, regardless of the expected-cost arithmetic. Jeb's choice, 2026-09-15 (D64). Set enabled to false to make the arithmetic the only proactive path"
            }
        },
        "self_directed": "kept in the assessment line for the record; not an input to resolution (D64: D40 measured it firing at 38 percent for sonnet against a 6 percent base rate, and the only row it disambiguated is gone)",
        "prior_failure": "kept: failed_at_xhigh still selects the frontier rung, as the escalation mechanism it always was",
        "buckets": buckets,
    }


def render(doc: dict) -> str:
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str]) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="write nothing; exit 1 if the committed file drifted")
    args = ap.parse_args(argv)

    doc = build_priors()
    rendered = render(doc)

    if args.check:
        current = PRIORS_PATH.read_text(encoding="utf-8") if PRIORS_PATH.exists() else None
        if current == rendered:
            print(f"{PRIORS_PATH.relative_to(REPO)} matches the generator")
            return 0
        print(f"{PRIORS_PATH.relative_to(REPO)} does not match the generator; "
              f"re-run without --check and commit the result", file=sys.stderr)
        return 1

    PRIORS_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    for k, b in doc["buckets"].items():
        f = b["floor"]
        rung = b["rungs_given_failure_below"].get("worker-opus-high")
        print(f"{k:32} floor mean {f['mean']:.3f} n_eff {f['n_eff']:2} {f['kind']:16} | "
              f"opus-high|fail {rung['mean']:.2f} {rung['kind']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
