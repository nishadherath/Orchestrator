"""Validate this probe's public citations without starting a provider call."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import probe
from test.harness.controller_x3_pair_tests import prepare
from test.harness.controller_x4_assessment_tests import AssessmentTests
from tools import controller_public_assessment
from tools.controller_wsl_interpreter import WslPublicInterpreter


with tempfile.TemporaryDirectory(prefix="x4-public-citation-preflight-") as raw:
    executor, root, _ = prepare(Path(raw) / "actor", "C03-D1")
    options = AssessmentTests().inputs(executor, root)
    packet = controller_public_assessment.collect(
        executor.project, issue=options["issue"],
        source_paths=options["source_paths"],
        quote_requests=[{"source": source, "quote": quote}
                        for source, quote in probe.QUOTES],
        input_revision=executor.status(root)["definition"]["input_revision"])
    WslPublicInterpreter(
        distro="kali-linux", linux_user="wsl",
        claude_path="/opt/orchestrator-worker-runtime/bin/claude",
        allowance_usd=.5).preflight()
    print(json.dumps({"citation_count": len(packet["citations"]),
                      "packet_schema": packet["schema_version"],
                      "provider_calls": 0}))
