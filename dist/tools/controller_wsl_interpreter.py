"""Tool-free, subscription-authenticated public assessment in WSL Claude Code.

The N1 executor owns admission and settlement. This adapter sees only the
bounded public packet, sends it on stdin, and returns one structured response
with terminal identity and charge telemetry. It never receives an API key.
"""
from __future__ import annotations

import base64
import json
import math
import os
import re
import subprocess
import time
from pathlib import Path, PurePosixPath

import claudep
import controller_policy
import controller_public_assessment as public
import model_registry
import worker_selector


PROMPT = Path(__file__).resolve().parent.parent / "src" / "System" / "PUBLIC_ASSESSMENT_PROMPT.md"
LAUNCHER = Path(__file__).resolve().with_name("controller_wsl_launch.py")
_SAFE_HOST_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
_FIELD_CHOICES = {
    "task_kind": ("implementation", "investigation"),
    "complexity": tuple(worker_selector.PRIORS),
    "verification": ("executable", "manual", "none"),
    "failure_cause": tuple(sorted(worker_selector.FAILURES)),
    "frame_confidence": ("clear", "uncertain"),
    "consequence": controller_policy.CONSEQUENCE,
    "premise_uncertainty": controller_policy.PREMISE_UNCERTAINTY,
    "alternatives": controller_policy.ALTERNATIVES,
    "constraint_coupling": controller_policy.COUPLING,
    "verification_gap": controller_policy.VERIFICATION_GAP,
    "observed_failure_cause": controller_policy.FAILURE_CAUSE,
    "required_output": controller_policy.REQUIRED_OUTPUT,
    "evidence_availability": controller_policy.EVIDENCE_AVAILABILITY,
}


def _schema(packet: dict) -> dict:
    ids = [row["id"] for row in packet["citations"]]
    id_array = {"type": "array", "items": {"type": "string", "enum": ids},
                "minItems": 1, "uniqueItems": True}
    return {
        "type": "object", "additionalProperties": False,
        "required": ["schema_version", "classifications", "field_evidence",
                     "material_evidence"],
        "properties": {
            "schema_version": {"const": 1},
            "classifications": {
                "type": "object", "additionalProperties": False,
                "required": sorted(_FIELD_CHOICES),
                "properties": {name: {"type": "string", "enum": list(choices)}
                               for name, choices in _FIELD_CHOICES.items()}},
            "field_evidence": {
                "type": "object", "additionalProperties": False,
                "required": sorted(_FIELD_CHOICES),
                "properties": {name: id_array for name in _FIELD_CHOICES}},
            "material_evidence": {
                "type": "array", "items": {"type": "string", "enum": ids},
                "uniqueItems": True},
        },
    }


class WslPublicInterpreter:
    """One WSL Claude Code call after a provider-free Claude.ai preflight."""

    def __init__(self, *, distro: str, linux_user: str, claude_path: str,
                 allowance_usd: float,
                 timeout_s: float = 180, launcher_path: str | None = None,
                 runner=None):
        if (not isinstance(distro, str) or not _SAFE_HOST_NAME.fullmatch(distro)
                or not isinstance(linux_user, str)
                or not _SAFE_HOST_NAME.fullmatch(linux_user)):
            raise ValueError("WSL distro and user must be safe host identifiers")
        if not isinstance(claude_path, str):
            raise ValueError("WSL Claude Code path must be a string")
        executable = PurePosixPath(claude_path)
        if (not executable.is_absolute()
                or executable.name != "claude" or ".." in executable.parts):
            raise ValueError("WSL Claude Code path must name an absolute claude binary")
        if (type(allowance_usd) not in (int, float)
                or not math.isfinite(allowance_usd) or allowance_usd <= 0
                or type(timeout_s) not in (int, float)
                or not math.isfinite(timeout_s) or timeout_s <= 0):
            raise ValueError("public interpreter allowance and timeout must be positive")
        self.distro = distro
        self.linux_user = linux_user
        self.claude_path = claude_path
        if launcher_path is None:
            host = LAUNCHER.resolve()
            if not host.drive or not host.drive.endswith(":"):
                raise ValueError("WSL launcher needs an explicit Linux path on this host")
            launcher_path = "/mnt/" + host.drive[0].lower() + "/" + "/".join(host.parts[1:])
        launch = PurePosixPath(launcher_path)
        if (not launch.is_absolute() or launch.name != "controller_wsl_launch.py"
                or ".." in launch.parts):
            raise ValueError("WSL launcher path is invalid")
        self.launcher_path = str(launch)
        self.allowance_usd = allowance_usd
        self.timeout_s = timeout_s
        self.runner = runner or subprocess.run
        self.cell = model_registry.resolve_role_profile("standard")["roles"]["controller"][0]
        self._preflight_ok = False

    def _prefix(self) -> list[str]:
        return ["wsl.exe", "-d", self.distro, "-u", self.linux_user, "--",
                "/usr/bin/env", "-C", "/tmp"]

    @staticmethod
    def _environment() -> dict[str, str]:
        # WSL reads its own private Claude.ai login. Never forward Windows
        # provider keys, model overrides or a caller-supplied WSLENV bridge.
        return {name: os.environ[name] for name in
                ("PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP", "USERPROFILE")
                if name in os.environ}

    def preflight(self) -> None:
        """Check subscription auth before N1 reserves any provider allowance."""
        self._preflight_ok = False
        try:
            proc = self.runner(
                [*self._prefix(), self.claude_path, "auth", "status", "--json"],
                capture_output=True, text=True, encoding="utf-8",
                errors="replace", env=self._environment(), timeout=30)
            state = json.loads(proc.stdout)
        except (OSError, subprocess.TimeoutExpired, TypeError, ValueError) as exc:
            raise public.PublicAssessmentError("WSL Claude.ai auth preflight unavailable") from exc
        if (proc.returncode != 0 or not isinstance(state, dict)
                or state.get("loggedIn") is not True
                or state.get("authMethod") != "claude.ai"
                or not isinstance(state.get("subscriptionType"), str)
                or not state["subscriptionType"]):
            raise public.PublicAssessmentError("WSL Claude.ai subscription auth is not ready")
        try:
            access = self.runner(
                [*self._prefix(), "/usr/bin/test", "-r", self.launcher_path],
                capture_output=True, text=True, encoding="utf-8",
                errors="replace", env=self._environment(), timeout=15)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise public.PublicAssessmentError("WSL launcher preflight unavailable") from exc
        if access.returncode != 0:
            raise public.PublicAssessmentError("WSL launcher is not readable")
        self._preflight_ok = True

    def __call__(self, packet: dict) -> dict:
        if not self._preflight_ok:
            raise public.PublicAssessmentError("WSL public interpreter needs auth preflight")
        packet = public._validate_packet(packet)
        try:
            system_prompt = PROMPT.read_text(encoding="utf-8")
        except OSError as exc:
            raise public.PublicAssessmentError("public assessment prompt is unavailable") from exc
        encoded_schema = base64.urlsafe_b64encode(json.dumps(
            _schema(packet), separators=(",", ":")).encode("utf-8")).decode("ascii")
        encoded_prompt = base64.urlsafe_b64encode(
            system_prompt.encode("utf-8")).decode("ascii")
        command = [*self._prefix(), "/usr/bin/python3", self.launcher_path,
                   self.claude_path, self.cell["cli_model"], self.cell["effort"],
                   str(self.allowance_usd), encoded_schema, encoded_prompt]
        payload = json.dumps(packet, sort_keys=True, ensure_ascii=False,
                             separators=(",", ":"))
        started = time.monotonic()
        try:
            proc = self.runner(command, input=payload, capture_output=True,
                               text=True, encoding="utf-8", errors="replace",
                               env=self._environment(), timeout=self.timeout_s)
            stdout = proc.stdout
        except subprocess.TimeoutExpired as exc:
            partial = claudep._result_from_stdout(
                exc.stdout, time.monotonic() - started, "WSL public assessment",
                stream_json=True)
            raise public.PublicInterpreterError(
                "WSL public assessment timed out", cost_usd=_cost(partial.cost_usd),
                terminal=False) from exc
        except OSError as exc:
            raise public.PublicInterpreterError("WSL public assessment did not start") from exc
        result = claudep._result_from_stdout(
            stdout, time.monotonic() - started, "WSL public assessment",
            stream_json=True)
        terminal = result.raw.get("type") == "result"
        cost = _cost(result.cost_usd)
        stderr = proc.stderr or ""
        if (proc.returncode != 0 and not (stdout or "").strip()
                and (stderr.startswith("Controller WSL launcher:")
                     or stderr.startswith("Error: --json-schema is not valid JSON:"))):
            # These local argument parsers reject before Claude contacts the
            # provider. Record a final zero charge instead of retaining a
            # false unresolved hold. Other failures remain uncertain.
            raise public.PublicInterpreterError(
                "WSL public assessment rejected before provider dispatch",
                cost_usd=0, terminal=True)
        if (proc.returncode != 0 or not terminal
                or result.raw.get("subtype") != "success"
                or result.extras.get("invalid_line_count") != 0):
            raise public.PublicInterpreterError(
                "WSL public assessment has no valid terminal success",
                cost_usd=cost, terminal=terminal and cost is not None)
        roots = result.extras.get("root_models")
        children = result.extras.get("child_models")
        if (not isinstance(roots, list) or len(roots) != 1
                or not isinstance(children, list)
                or not model_registry.identity_matches(
                    self.cell["name"], roots[0], children)):
            raise public.PublicInterpreterError(
                "WSL public assessment served model identity is unverified",
                cost_usd=cost, terminal=cost is not None)
        usage = result.extras.get("usage")
        if (cost is None or not isinstance(usage, dict)
                or any(type(usage.get(key)) is not int or usage[key] < 0
                       for key in ("input_tokens", "output_tokens"))):
            raise public.PublicInterpreterError(
                "WSL public assessment terminal billing is incomplete",
                cost_usd=cost, terminal=cost is not None)
        structured = result.raw.get("structured_output")
        if structured is None:
            try:
                structured = json.loads(result.result)
            except (TypeError, ValueError) as exc:
                raise public.PublicInterpreterError(
                    "WSL public assessment output is not structured JSON",
                    cost_usd=cost, terminal=True) from exc
        if not isinstance(structured, dict):
            raise public.PublicInterpreterError(
                "WSL public assessment output is not a JSON object",
                cost_usd=cost, terminal=True)
        return {
            "interpretation": structured,
            "telemetry": {"provider_calls": 1, "model": roots[0],
                          "cost_usd": cost, "input_tokens": usage["input_tokens"],
                          "output_tokens": usage["output_tokens"]},
        }


def _cost(value: object) -> float | None:
    if type(value) in (int, float) and math.isfinite(value) and value >= 0:
        return float(value)
    return None
