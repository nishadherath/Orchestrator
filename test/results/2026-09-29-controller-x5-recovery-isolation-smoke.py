"""Provider-free private mount smoke for the X5 recovery Controller."""

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from controller_x5_recovery_isolation import hidden_evaluation_tree  # noqa: E402


oracle = ROOT / "test/oracles/controller_x5_recovery/R01.json"
assert oracle.is_file()
with hidden_evaluation_tree(ROOT):
    result = {
        "root_sees_oracle": oracle.exists(),
        "controller_sees_oracle": subprocess.run(
            ["/usr/sbin/runuser", "-u", "wsl", "--", "/usr/bin/test", "-e", str(oracle)],
            check=False).returncode == 0,
        "system_prompt_visible": (ROOT / "src/System").is_dir(),
        "evaluation_tree_empty": not any((ROOT / "test").iterdir()),
    }
assert oracle.is_file()
assert result == {"root_sees_oracle": False, "controller_sees_oracle": False,
                  "system_prompt_visible": True, "evaluation_tree_empty": True}
print(json.dumps({"masked": result, "restored": True, "provider_calls": 0}))
