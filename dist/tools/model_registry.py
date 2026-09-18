#!/usr/bin/env python3
"""Validate and resolve every Claude model/effort cell from one registry."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY = ROOT / "src" / "model_registry.json"
DEFAULT_COSTS = ROOT / "src" / "cost_table.json"
ROLES = {"controller", "framer", "verifier", "generator", "critic", "selector", "librarian"}


class RegistryError(ValueError):
    """The registry cannot safely resolve a requested cell or profile."""


def load(path: Path = DEFAULT_REGISTRY) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError(f"cannot read model registry {path}: {exc}") from exc
    validate(value)
    return value


def validate(value: dict) -> None:
    if not isinstance(value, dict) or value.get("version") != 1:
        raise RegistryError("model registry needs version 1")
    models = value.get("model_order")
    efforts = value.get("effort_order")
    if models != ["sonnet", "opus", "fable"]:
        raise RegistryError("model_order must be sonnet, opus, fable")
    if efforts != ["low", "medium", "high", "xhigh", "max"]:
        raise RegistryError("effort_order must contain all five supported efforts")
    definitions = value.get("models")
    cells = value.get("cells")
    if not isinstance(definitions, dict) or set(definitions) != set(models):
        raise RegistryError("models must define every model exactly once")
    expected_cells = {f"worker-{model}-{effort}" for model in models for effort in efforts}
    if not isinstance(cells, dict) or set(cells) != expected_cells:
        raise RegistryError("cells must define the complete 3x5 matrix exactly once")
    for model, definition in definitions.items():
        if definition.get("supported_efforts") != efforts:
            raise RegistryError(f"{model} must declare all five supported efforts")
        for field in ("cli_model", "expected_provider_model"):
            if not isinstance(definition.get(field), str) or not definition[field]:
                raise RegistryError(f"{model}.{field} must be a non-empty string")
        pricing = definition.get("pricing")
        if not isinstance(pricing, dict) or pricing.get("status") not in {"known", "unknown"}:
            raise RegistryError(f"{model}.pricing needs an explicit known/unknown status")
        if pricing["status"] == "unknown" and any(
            pricing.get(field) is not None for field in ("input_per_million_usd", "output_per_million_usd")
        ):
            raise RegistryError(f"{model} unknown pricing cannot contain numeric prices")
    for name, cell in cells.items():
        expected_name = f"worker-{cell.get('model')}-{cell.get('effort')}"
        if name != expected_name or cell.get("model") not in models or cell.get("effort") not in efforts:
            raise RegistryError(f"invalid cell mapping: {name}")
        roles = cell.get("controller_roles")
        if not isinstance(roles, list) or not set(roles) <= ROLES:
            raise RegistryError(f"{name} has invalid controller_roles")
    qualification = value.get("cell_qualification")
    if (not isinstance(qualification, dict)
            or qualification.get("status") != "offline-wiring"
            or qualification.get("live_quality") != "unqualified"):
        raise RegistryError("cell_qualification must distinguish offline wiring from live quality")
    profiles = value.get("role_profiles")
    if not isinstance(profiles, dict) or "standard" not in profiles:
        raise RegistryError("role_profiles must include standard")
    for profile_name, profile in profiles.items():
        assignments = profile.get("roles") if isinstance(profile, dict) else None
        if not isinstance(assignments, dict) or set(assignments) != ROLES:
            raise RegistryError(f"profile {profile_name} must assign every role")
        for role, names in assignments.items():
            if not isinstance(names, list) or not names:
                raise RegistryError(f"profile {profile_name}.{role} needs at least one cell")
            for name in names:
                if name not in cells or role not in cells[name]["controller_roles"]:
                    raise RegistryError(f"profile {profile_name}.{role} cannot use {name}")


def models(registry: dict | None = None) -> tuple[str, ...]:
    value = registry or load()
    return tuple(value["model_order"])


def efforts(registry: dict | None = None) -> tuple[str, ...]:
    value = registry or load()
    return tuple(value["effort_order"])


def resolve_cell(name: str, registry: dict | None = None) -> dict:
    value = registry or load()
    try:
        cell = value["cells"][name]
        model = value["models"][cell["model"]]
    except (KeyError, TypeError) as exc:
        raise RegistryError(f"unsupported worker cell: {name}") from exc
    return {
        "name": name,
        "model": cell["model"],
        "effort": cell["effort"],
        "cli_model": model["cli_model"],
        "expected_provider_model": model["expected_provider_model"],
        "availability": dict(model["availability"]),
        "identity": dict(model["identity"]),
        "pricing": dict(model["pricing"]),
        "context_limit_tokens": model["context_limit_tokens"],
        "output_limit_tokens": model["output_limit_tokens"],
        "direct_worker": cell["direct_worker"],
        "controller_roles": list(cell["controller_roles"]),
        "qualification": dict(value["cell_qualification"]),
    }


def resolve_role_profile(name: str, registry: dict | None = None) -> dict:
    value = registry or load()
    try:
        profile = value["role_profiles"][name]
    except (KeyError, TypeError) as exc:
        raise RegistryError(f"unsupported Controller role profile: {name}") from exc
    return {
        "name": name,
        "status": profile["status"],
        "roles": {role: [resolve_cell(cell, value) for cell in cells]
                  for role, cells in profile["roles"].items()},
    }


def identity_matches(name: str, actual_model: str | None,
                     child_models: list[str] | None = None,
                     registry: dict | None = None) -> bool:
    expected = resolve_cell(name, registry)["expected_provider_model"]
    return actual_model == expected and not (child_models or [])


def projected_cost(name: str, costs_path: Path = DEFAULT_COSTS,
                   registry: dict | None = None) -> dict:
    resolve_cell(name, registry)
    try:
        row = json.loads(costs_path.read_text(encoding="utf-8")).get("cells", {}).get(name)
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError(f"cannot read cost table {costs_path}: {exc}") from exc
    amount = row.get("cost_per_run_usd") if isinstance(row, dict) else None
    wall = row.get("wall_clock_s") if isinstance(row, dict) else None
    known = (isinstance(amount, (int, float)) and not isinstance(amount, bool)
             and isinstance(wall, (int, float)) and not isinstance(wall, bool))
    return {"cell": name, "known": known,
            "cost_per_run_usd": amount if known else None,
            "wall_clock_s": wall if known else None,
            "provenance": row.get("provenance") if isinstance(row, dict) else None}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--cell")
    parser.add_argument("--profile")
    args = parser.parse_args(argv)
    try:
        registry = load()
        if args.cell:
            print(json.dumps({**resolve_cell(args.cell, registry),
                              "projection": projected_cost(args.cell, registry=registry)}, indent=2))
        elif args.profile:
            print(json.dumps(resolve_role_profile(args.profile, registry), indent=2))
        else:
            print(f"model registry: OK, {len(registry['cells'])} cells, "
                  f"{len(registry['role_profiles'])} role profiles")
        return 0
    except RegistryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
