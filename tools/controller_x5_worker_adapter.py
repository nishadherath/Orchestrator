"""X5 evaluation host using the already installed Q4R three-cell boundary.

Q3 deliberately remains a two-cell historical contract. Q4R admits the N3
Sonnet High prior and requires a schema-bound final report, while retaining
Q1 staging, subscription isolation, and exact multi-file collection.
"""
from __future__ import annotations

from pathlib import Path

import worker_wsl_q4r_adapter as q4r
from worker_adapter import CapabilityError
from worker_q4r_structured import schema_argument


class X5WslAdapter(q4r.Q4RWslAdapter):
    """Pin the installed Q4R launcher and schema to this X5 source package."""

    def capability(self, actor_root: Path) -> dict:
        result = super().capability(actor_root)
        source = Path(__file__).resolve().with_name("worker_wsl_namespace_q4r.sh")
        installed_schema = q4r.RUNTIME / "q4r-report-schema.json"
        if (q4r.sha(source.read_bytes()) != result["q4r_launcher_sha256"]
                or installed_schema.read_text(encoding="utf-8").strip()
                != schema_argument().removeprefix("--json-schema=")):
            raise CapabilityError("installed Q4R host differs from frozen X5 source")
        result["experimental_host_profile"] = "x5-q4r-three-cell-v2"
        result["max_single_call_usd"] = 6.0
        return result
