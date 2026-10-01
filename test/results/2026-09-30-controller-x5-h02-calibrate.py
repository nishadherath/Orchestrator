"""Provider-free H02 calibration across public, protected and upstream checks."""

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CASE = ROOT / "test/fixtures/controller_x5_authored_pytest/development/H02"
ACTOR = CASE / "actor"
ORACLE = ROOT / "test/oracles/controller_x5_authored_pytest/H02"
OUTPUT = ROOT / "test/results/2026-09-30-controller-x5-h02-calibration"
EXPECTED_PLUGIN = {
    "baseline": "ba47c25a4a22b117891e9214940729c41af936d3dafbb18b4284de8a88ed3375",
    "proposal": "558f5ab0e7c357d253f26ccb34df3779a04f39db778a94188f843e316c8e6fd2",
    "narrow_control": "121696c4633991eeccc1284919031f732f8a285cf1bc6c0265637f9d30952513",
}
EXPECT = {
    "baseline": {"public": False, "forward": False, "reverse": False,
                 "no_hook": True, "upstream": True},
    "narrow_control": {"public": True, "forward": False, "reverse": False,
                       "no_hook": True},
    "proposal": {"public": True, "forward": True, "reverse": True,
                 "no_hook": True, "upstream": True},
    "alternative": {"public": True, "forward": True, "reverse": True,
                    "no_hook": True, "upstream": True},
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wsl(path: Path) -> str:
    resolved = path.resolve()
    if resolved.drive.upper() != "C:":
        raise ValueError(f"unexpected host drive: {resolved}")
    return "/mnt/c" + resolved.as_posix()[2:]


def run(variant: str, phase: str, source: Path) -> dict:
    environment = [
        f"PYTHONPATH={wsl(source)}:{wsl(ACTOR / 'deps')}:{wsl(ACTOR / 'deps/pygments-runtime.zip')}",
        "PYTHONDONTWRITEBYTECODE=1",
    ]
    options = ["-q", "-p", "no:cacheprovider"]
    if phase != "upstream":
        environment.append("PYTEST_DISABLE_PLUGIN_AUTOLOAD=1")
        options += ["-p", "pytest_asyncio.plugin"]
    if phase in {"forward", "reverse"}:
        environment.append("X5_EXPECT_SYNC_VARIANTS=1")
    if phase == "public":
        targets = [wsl(ACTOR / "case/test_mre.py")]
    elif phase == "forward":
        targets = [wsl(ORACLE / "forward")]
    elif phase == "reverse":
        target = wsl(ORACLE / "forward/test_factory_scope.py")
        targets = [target + "::test_sync_using_async_fixture", target + "::test_async"]
    elif phase == "no_hook":
        targets = [wsl(ORACLE / "no_hook")]
    elif phase == "upstream":
        targets = [wsl(ORACLE / "upstream/test_loop_factory_parametrization.py")]
    else:
        raise ValueError(f"unknown phase: {phase}")
    command = ["wsl.exe", "-d", "kali-linux", "-u", "root", "--", "env",
               *environment, "python3", "-B", "-m", "pytest", *options, *targets]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True,
                            timeout=120, check=False)
    log = OUTPUT / f"{variant}-{phase}.log"
    log.write_text(result.stdout + "\n[stderr]\n" + result.stderr, encoding="utf-8")
    expected = EXPECT[variant][phase]
    observed = result.returncode == 0
    return {
        "phase": phase,
        "exit_code": result.returncode,
        "expected_pass": expected,
        "observed_pass": observed,
        "matched": expected == observed,
        "log": str(log.relative_to(ROOT)).replace("\\", "/"),
        "log_sha256": sha(log),
        "tail": (result.stdout + result.stderr).splitlines()[-4:],
    }


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    inventory = json.loads((ACTOR / "SOURCE.json").read_text(encoding="utf-8"))
    for name, expected in inventory["files"].items():
        if sha(ACTOR / name) != expected:
            raise ValueError(f"actor dependency drifted: {name}")
    rows: list[dict] = []
    for variant, phases in EXPECT.items():
        source = ACTOR if variant == "baseline" else CASE / "variants" / variant
        plugin_sha = sha(source / "pytest_asyncio/plugin.py")
        if variant in EXPECTED_PLUGIN and plugin_sha != EXPECTED_PLUGIN[variant]:
            raise ValueError(f"{variant} plugin source drifted")
        checks = [run(variant, phase, source) for phase in phases]
        rows.append({"variant": variant, "plugin_sha256": plugin_sha,
                     "checks": checks, "matched": all(c["matched"] for c in checks)})
        print(json.dumps({"variant": variant, "matched": rows[-1]["matched"]}), flush=True)
    receipt = {
        "schema_version": 1,
        "case": "H02 authored development, unfrozen",
        "host": "kali-linux WSL, Python 3.14.7",
        "provider_calls": 0,
        "actor_inventory_sha256": sha(ACTOR / "SOURCE.json"),
        "oracle_files": {
            str(path.relative_to(ORACLE)).replace("\\", "/"): sha(path)
            for path in sorted(ORACLE.rglob("*.py"))
        },
        "rows": rows,
        "qualified": all(row["matched"] for row in rows),
    }
    path = ROOT / "test/results/2026-09-30-controller-x5-h02-calibration.json"
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"qualified": receipt["qualified"], "result": str(path)}))
    if not receipt["qualified"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
