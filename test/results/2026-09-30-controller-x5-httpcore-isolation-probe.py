"""Provider-free H01 actor check in the existing unprivileged Q1 namespace."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import worker_wsl_q2_verify as q2  # noqa: E402


CASE = ROOT / "test/fixtures/controller_x5_authored_httpcore/development/H01"
ORACLE = ROOT / "test/oracles/controller_x5_authored_httpcore/H01_hidden.py"
RESULT = ROOT / "test/results/2026-09-30-controller-x5-httpcore-isolation.json"


def probe(label: str) -> dict:
    overlay = None if label == "baseline" else CASE / "variants" / label
    package, manifest_path, manifest = q2.copy_package(CASE / "actor", overlay)
    uncertain = False
    try:
        denial = q2.run_isolated(
            package, manifest_path, manifest,
            ["/usr/bin/python3", "-B", "-c",
             "from pathlib import Path;import sys;"
             "\ntry: Path(sys.argv[1]).read_bytes()"
             "\nexcept OSError: print('DENIED')"
             "\nelse: print('EXPOSED')", str(ORACLE)],
        )
        public = q2.run_isolated(
            package, manifest_path, manifest,
            ["/usr/bin/python3", "-B", "public_check.py"],
        )
        return {"variant": label, "oracle_read_denied": denial.returncode == 0
                and denial.stdout.strip() == "DENIED",
                "public_passed": public.returncode == 0,
                "public_exit_code": public.returncode,
                "public_tail": (public.stdout + public.stderr)[-900:]}
    except q2.UncertainActorError:
        uncertain = True
        raise
    finally:
        if not uncertain:
            q2.dispose(package, q2.SEEDS)
            manifest_path.unlink(missing_ok=True)


def main() -> None:
    if os.name != "posix" or os.geteuid() != 0:
        raise RuntimeError("H01 isolation probe requires WSL root")
    rows = [probe(label) for label in ("baseline", "partial", "reference", "alternative")]
    expected = {"baseline": False, "partial": True,
                "reference": True, "alternative": True}
    qualified = all(row["oracle_read_denied"] and
                    row["public_passed"] == expected[row["variant"]] for row in rows)
    body = {"schema_version": 1, "case": "H01", "qualified": qualified,
            "boundary": "Q1 isolated actor uid 65534; root-owned evaluator oracle",
            "rows": rows}
    RESULT.write_text(json.dumps(body, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"qualified": qualified,
                      "rows": [{"variant": row["variant"],
                                "oracle_read_denied": row["oracle_read_denied"],
                                "public_passed": row["public_passed"]}
                               for row in rows]}, sort_keys=True))
    if not qualified:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
