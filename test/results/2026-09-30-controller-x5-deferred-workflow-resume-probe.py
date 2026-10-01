"""Provider-free probe of a second workflow call after deferred handoff."""

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))

import controller_workflow
from test.harness.controller_routing_r4_tests import FakeAdapter as FakeController
from test.harness.controller_x3_pair_tests import interpret_public, prepare
from test.harness.controller_x4_assessment_tests import AssessmentTests


def run_case(second_adapter: bool) -> dict:
    with tempfile.TemporaryDirectory(prefix="x5-deferred-resume-") as raw:
        executor, root, worker = prepare(Path(raw) / "actor", "N04-D1")
        controller = FakeController()
        options = AssessmentTests().inputs(executor, root)
        options["assessment_allowance_usd"] = options.pop("maximum_usd")

        def execute(defer_worker: bool, adapter) -> dict:
            return controller_workflow.execute(
                executor, root, interpreter=interpret_public,
                controller_adapter=adapter, explicit_mode="on",
                worker_attempt_limit=1, defer_worker=defer_worker, **options)

        first = execute(True, controller)
        try:
            second = execute(False, controller if second_adapter else None)
            second_outcome = {"return_state": second["task"]["state"],
                              "dispatch_stage": second["dispatch"]["stage"]
                              if second["dispatch"] else None}
        except Exception as exc:
            second_outcome = {"exception_type": type(exc).__name__,
                              "exception": str(exc)}
        status = executor.status(root)
        return {
            "first_state": first["task"]["state"],
            "first_dispatch_stage": first["dispatch"]["stage"],
            "second": second_outcome,
            "final_state": status["state"],
            "controller_calls": controller.calls,
            "worker_calls": len(worker.calls),
            "controller_admission_status": status["controller_admission"]["status"],
            "budget_unresolved": status["budget"]["unresolved"],
        }


def main() -> None:
    print(json.dumps({"same_adapter": run_case(True),
                      "missing_adapter": run_case(False)}, sort_keys=True))


if __name__ == "__main__":
    main()
