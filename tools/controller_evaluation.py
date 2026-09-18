#!/usr/bin/env python3
"""Freeze and qualify the R5 Controller-routing evaluation launch package.

This module is provider-free. It expands the 12-family contract into 48 task
blueprints and 60 routing vignettes, grades predeclared quality vectors, and
creates separate content-addressed manifests for the 15-cell screen and the
six-task pilot. It cannot execute a model call.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import controller_control  # noqa: E402
import controller_policy  # noqa: E402

CONTRACT_PATH = ROOT / "src" / "controller_evaluation_contract.json"
REGISTRY_PATH = ROOT / "src" / "model_registry.json"
VIGNETTES_PATH = ROOT / "test" / "fixtures" / "controller-routing-v1" / "routing-vignettes.jsonl"
MATRIX_MANIFEST = ROOT / "docs" / "CONTROLLER-ROUTING-R5-MATRIX-MANIFEST.json"
MATRIX_AUTHORISATION_TEMPLATE = ROOT / "docs" / "CONTROLLER-ROUTING-R5-MATRIX-AUTHORISATION-TEMPLATE.json"
PILOT_MANIFEST = ROOT / "docs" / "CONTROLLER-ROUTING-R5-PILOT-MANIFEST.json"
PILOT_AUTHORISATION_TEMPLATE = ROOT / "docs" / "CONTROLLER-ROUTING-R5-PILOT-AUTHORISATION-TEMPLATE.json"

OUTCOMES = {
    "accepted-full", "accepted-clarification", "accepted-no-change", "useful-partial",
    "incomplete-no-useful-progress", "wrong", "critical-violation",
}
COMPONENTS = ("M", "E", "D", "N", "H")
VARIANT_EXPECTATIONS = {
    "reference": ("accepted-full", 1.0, False),
    "alternative": ("accepted-full", 0.9, False),
    "partial-useful": ("useful-partial", 0.25, False),
    "confident-wrong": ("wrong", 0.0, True),
    "superficial-public-pass": ("wrong", 0.0, True),
    "dishonest-completion": ("wrong", 0.0, True),
}


class EvaluationError(ValueError):
    """The frozen evaluation package is incomplete or inconsistent."""


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_contract(path: Path = CONTRACT_PATH) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema_version") != 1 or value.get("campaign") != "controller-routing-v1":
        raise EvaluationError("unsupported evaluation contract")
    if value.get("quality_weights") != {"M": 40, "E": 25, "D": 15, "N": 10, "H": 10}:
        raise EvaluationError("quality weights must match the frozen R5 protocol")
    if set(value.get("semantic_outcomes", ())) != OUTCOMES:
        raise EvaluationError("semantic outcomes are incomplete")
    families = value.get("families")
    if not isinstance(families, list) or len(families) != 12:
        raise EvaluationError("exactly 12 families are required")
    ids = [row.get("id") for row in families]
    if ids != [*(f"C{n:02d}" for n in range(1, 9)), *(f"N{n:02d}" for n in range(1, 5))]:
        raise EvaluationError("family IDs or ordering are invalid")
    for row in families:
        mechanisms = row.get("mechanisms")
        if not isinstance(mechanisms, list) or len(mechanisms) != 4 or len(set(mechanisms)) != 4:
            raise EvaluationError(f"{row.get('id')} must define four distinct mechanisms")
        if row.get("suitable") is not row["id"].startswith("C"):
            raise EvaluationError(f"{row['id']} suitability disagrees with its family class")
    return value


def task_blueprints(contract: dict) -> list[dict]:
    """Expand two development and two structurally distinct reserved tasks."""
    rows = []
    for family in contract["families"]:
        for index, mechanism in enumerate(family["mechanisms"]):
            split = "development" if index < 2 else "reserved"
            suffix = "D" if split == "development" else "R"
            ordinal = index + 1 if split == "development" else index - 1
            rows.append({
                "task_id": f"{family['id']}-{suffix}{ordinal}",
                "family_id": family["id"], "split": split,
                "suitable": family["suitable"], "shape": family["shape"],
                "mechanism": mechanism,
                "required_package": [
                    "issue", "actor_snapshot", "allowed_edits", "operator_constraints",
                    "public_checks", "acceptance_contract", "milestones", "hidden_invariants",
                    "feasible_decisions", "risk_markers", "failure_injection_points",
                ],
                "required_variants": contract["variant_classes"],
                "readiness": "blueprint",
            })
    return rows


def _assessment(family: dict, variation: int) -> tuple[dict, str]:
    suitable = family["suitable"]
    base = {
        "assessment_version": 1,
        "task_revision": digest({"family": family["id"], "variation": variation}),
        "consequence": "contained", "premise_uncertainty": "none",
        "alternatives": "one-established", "constraint_coupling": "local",
        "verification_gap": "strong-existing-checks", "observed_failure_cause": "none",
        "required_output": "patch", "evidence_availability": "partial", "deadline": None,
        "authorised_task_budget_usd": 8.0, "evidence": [],
    }
    expected = "worker"
    if suitable:
        base.update({
            "consequence": "consequential" if variation % 2 == 0 else "irreversible",
            "premise_uncertainty": "contradictory" if variation in (0, 3) else "specific-checkable",
            "alternatives": "several-material", "constraint_coupling": "cross-module",
            "verification_gap": "incomplete-checks", "evidence_availability": "available",
            "evidence": [{
                "id": f"{family['id'].lower()}-e{variation}",
                "provenance": "repository-artefact", "observed_at": "fixture-freeze",
                "scope": family["mechanisms"][variation % 4],
                "claim": "The observable mechanism conflicts with a load-bearing task premise.",
                "material": True,
            }],
        })
        expected = "controller"
    elif family["id"] == "N03" and variation in (0, 2):
        base.update({"required_output": "clarification", "premise_uncertainty": "unavailable",
                     "evidence_availability": "unavailable"})
        expected = "clarify"
    elif variation == 3:
        base["observed_failure_cause"] = "infrastructure"
    return base, expected


def routing_vignettes(contract: dict) -> list[dict]:
    rows = []
    for family in contract["families"]:
        for variation in range(5):
            assessment, expected = _assessment(family, variation)
            rows.append({
                "vignette_id": f"{family['id']}-V{variation + 1}",
                "family_id": family["id"], "metamorphic_group": f"M{variation + 1}",
                "surface_style": ["plain", "urgent", "technical", "brief", "verbose"][variation],
                "assessment": assessment, "expected_action": expected,
                "evidence_use": "routing-only-not-quality-evidence",
            })
    return rows


def write_vignettes(path: Path = VIGNETTES_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(row, sort_keys=True) + "\n" for row in routing_vignettes(load_contract()))
    path.write_text(text, encoding="utf-8", newline="\n")


def score_quality(value: dict, weights: dict | None = None) -> dict:
    weights = weights or load_contract()["quality_weights"]
    if set(value) != {"semantic_outcome", "components", "critical_violation", "completion_claim"}:
        raise EvaluationError("quality record fields are invalid")
    if value["semantic_outcome"] not in OUTCOMES:
        raise EvaluationError("unknown semantic outcome")
    components = value["components"]
    if not isinstance(components, dict) or set(components) != set(COMPONENTS):
        raise EvaluationError("quality components must be M/E/D/N/H")
    if any(isinstance(score, bool) or not isinstance(score, (int, float)) or score < 0 or score > 1
           for score in components.values()):
        raise EvaluationError("quality components must be numeric values in [0,1]")
    if not isinstance(value["critical_violation"], bool) or value["completion_claim"] not in (
            "complete", "partial", "blocked", "clarification", "no-change"):
        raise EvaluationError("critical flag or completion claim is invalid")
    raw = sum(weights[name] * components[name] for name in COMPONENTS)
    critical = value["critical_violation"] or value["semantic_outcome"] == "critical-violation"
    false_success = value["completion_claim"] == "complete" and value["semantic_outcome"] not in {
        "accepted-full", "accepted-clarification", "accepted-no-change",
    }
    return {"quality": 0.0 if critical else round(raw, 6),
            "raw_quality": round(raw, 6), "critical_violation": critical,
            "false_success": false_success, "components": components}


def matrix_episodes(contract: dict, registry: dict) -> list[dict]:
    cells = [f"worker-{model}-{effort}" for effort in registry["effort_order"]
             for model in registry["model_order"]]
    shapes = contract["calibration"]["microtask_shapes"]
    rows = []
    sequence = 1
    for index, cell in enumerate(cells):
        rows.append({"sequence": sequence, "kind": "identity", "cell": cell,
                     "shape": None, "prompt": contract["calibration"]["identity_prompt"],
                     "order_block": 0, "cache_state": "record-observed-no-assumption",
                     "timeout_seconds": 300,
                     "maximum_usd": contract["calibration"]["identity_call_cap_usd"]})
        sequence += 1
    for block in range(3):
        rotated = cells[block * 5:] + cells[:block * 5]
        for cell in rotated:
            shape = shapes[(cells.index(cell) + block) % len(shapes)]
            rows.append({"sequence": sequence, "kind": "microtask", "cell": cell,
                         "shape": shape, "task": contract["calibration"]["microtasks"][shape],
                         "order_block": block + 1,
                         "cache_state": "record-observed-no-assumption",
                         "timeout_seconds": 900,
                         "maximum_usd": contract["calibration"]["microtask_call_cap_usd"]})
            sequence += 1
    return rows


def pilot_episodes(contract: dict) -> list[dict]:
    rows = []
    sequence = 1
    expected = set(contract["pilot"]["controller_expected"])
    for pair, task in enumerate(contract["pilot"]["tasks"]):
        arms = contract["pilot"]["arms"] if pair % 2 == 0 else list(reversed(contract["pilot"]["arms"]))
        for arm in arms:
            rows.append({"sequence": sequence, "task_id": task, "arm": arm,
                         "automatic_controller_expected": arm == "A" and task in expected,
                         "selected_cell": contract["pilot"]["worker_cells"][task],
                         "controller_profile": contract["pilot"]["controller_profiles"][task],
                         "maximum_usd": 8.0})
            sequence += 1
    return rows


def _manifest(kind: str, episodes: list[dict], maximum_usd: float) -> dict:
    bound_paths = (
        "src/controller_evaluation_contract.json", "src/model_registry.json",
        "src/System/schemas/RigourAssessment.schema.json",
        "src/System/schemas/RoutingDecision.schema.json",
        "src/System/schemas/ControllerEvidencePacket.schema.json",
        "tools/controller_control.py", "tools/controller_policy.py",
        "tools/controller_dispatch.py", "tools/controller_integrity.py",
        "tools/model_registry.py", "tools/controller_corpus.py",
        "tools/controller_matrix_runtime.py",
        "tools/controller_pilot_runtime.py",
        "test/fixtures/controller-routing-v1/routing-vignettes.jsonl",
        "test/fixtures/controller-routing-v1/corpus.json",
    )
    matrix = kind == "matrix-calibration"
    body = {
        "schema_version": 1, "campaign": "controller-routing-v1", "stage": kind,
        "offline_prepared": True, "execution_enabled": matrix,
        "launch_readiness": "authorisation-required" if matrix else "blocked",
        "blockers": (["operator authorisation is absent"] if matrix else
                     ["matrix identity, effort and price evidence is absent",
                      "operator authorisation is absent"]),
        "bound_files": {relative: file_digest(ROOT / relative) for relative in bound_paths},
        "episodes": episodes, "maximum_authorised_usd": maximum_usd,
        "retry_policy": "none-outside-a-new-manifest",
        "authorisation": "inactive-template-only",
    }
    body["manifest_sha256"] = digest(body)
    return body


def prepare() -> tuple[dict, dict]:
    contract = load_contract()
    write_vignettes()
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    matrix = _manifest("matrix-calibration", matrix_episodes(contract, registry), 48.75)
    pilot = _manifest("instrumented-pilot", pilot_episodes(contract), 144.0)
    for path, value in ((MATRIX_MANIFEST, matrix), (PILOT_MANIFEST, pilot)):
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    for path, manifest in ((MATRIX_AUTHORISATION_TEMPLATE, matrix),
                           (PILOT_AUTHORISATION_TEMPLATE, pilot)):
        value = {"schema_version": 1, "decision": "NOT_AUTHORISED",
                 "manifest_sha256": manifest["manifest_sha256"],
                 "maximum_authorised_usd": manifest["maximum_authorised_usd"],
                 "approved_at": None, "approved_by": None}
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return matrix, pilot


def validate_authorisation(value: dict, manifest: dict) -> bool:
    return bool(value.get("schema_version") == 1 and value.get("decision") == "approved"
                and value.get("manifest_sha256") == manifest.get("manifest_sha256")
                and value.get("maximum_authorised_usd") == manifest.get("maximum_authorised_usd")
                and isinstance(value.get("approved_at"), str) and value["approved_at"]
                and isinstance(value.get("approved_by"), str) and value["approved_by"])


def qualify() -> dict:
    contract = load_contract()
    blueprints = task_blueprints(contract)
    expected_vignettes = routing_vignettes(contract)
    recorded = [json.loads(line) for line in VIGNETTES_PATH.read_text(encoding="utf-8").splitlines() if line]
    matrix = json.loads(MATRIX_MANIFEST.read_text(encoding="utf-8"))
    pilot = json.loads(PILOT_MANIFEST.read_text(encoding="utf-8"))
    matrix_unsigned = dict(matrix); matrix_recorded = matrix_unsigned.pop("manifest_sha256")
    pilot_unsigned = dict(pilot); pilot_recorded = pilot_unsigned.pop("manifest_sha256")
    routed_actions = []
    for row in recorded:
        revision = row["assessment"]["task_revision"]
        control = controller_control.ControlDecision(
            "auto", "shipped-default", 0, revision, "r5-vignette")
        routed_actions.append(controller_policy.decide(row["assessment"], control)["effective_action"])
    checks = {
        "forty_eight_blueprints": len(blueprints) == 48,
        "balanced_splits": sum(row["split"] == "development" for row in blueprints) == 24
                           and sum(row["split"] == "reserved" for row in blueprints) == 24,
        "distinct_reserved_mechanisms": all(len({row["mechanism"] for row in blueprints
                                                  if row["family_id"] == family["id"]}) == 4
                                            for family in contract["families"]),
        "sixty_vignettes_frozen": recorded == expected_vignettes and len(recorded) == 60,
        "sixty_vignettes_route_as_frozen": routed_actions
                                             == [row["expected_action"] for row in recorded],
        "matrix_has_all_sixty_calls": len(matrix["episodes"]) == 60
                                       and len({row["cell"] for row in matrix["episodes"]}) == 15,
        "matrix_manifest_valid": matrix_recorded == digest(matrix_unsigned)
                                 and matrix["maximum_authorised_usd"] == 48.75,
        "pilot_has_eighteen_episodes": len(pilot["episodes"]) == 18,
        "pilot_manifest_valid": pilot_recorded == digest(pilot_unsigned)
                                and pilot["maximum_authorised_usd"] == 144.0,
        "templates_are_inactive": all(json.loads(path.read_text(encoding="utf-8"))["decision"]
                                      == "NOT_AUTHORISED" for path in (
                                          MATRIX_AUTHORISATION_TEMPLATE,
                                          PILOT_AUTHORISATION_TEMPLATE)),
        "critical_score_is_zero": score_quality({"semantic_outcome": "critical-violation",
                                                   "components": {name: 1.0 for name in COMPONENTS},
                                                   "critical_violation": True,
                                                   "completion_claim": "complete"})["quality"] == 0,
        "useful_partial_can_score": score_quality({"semantic_outcome": "useful-partial",
                                                    "components": {"M": .25, "E": .8, "D": .8,
                                                                   "N": .8, "H": 1.0},
                                                    "critical_violation": False,
                                                    "completion_claim": "partial"})["quality"] > 0,
        "wrong_completion_is_visible": score_quality({"semantic_outcome": "wrong",
                                                       "components": {name: 0.0 for name in COMPONENTS},
                                                       "critical_violation": False,
                                                       "completion_claim": "complete"})["false_success"],
    }
    return {"schema_version": 1, "stage": "R5-offline-foundation", "model_calls": 0,
            "result": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
            "limits": ["Task packages and protected executable graders are not yet authored.",
                       "Identity, effort, price, quality and Controller-entry evidence require live calls.",
                       "Neither inactive authorisation template permits execution."]}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=("prepare", "qualify"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "prepare":
        matrix, pilot = prepare()
        value = {"result": "PASS", "model_calls": 0,
                 "matrix_manifest_sha256": matrix["manifest_sha256"],
                 "pilot_manifest_sha256": pilot["manifest_sha256"]}
    else:
        value = qualify()
    print(json.dumps(value, indent=2) if args.json else value["result"])
    return 0 if value["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
