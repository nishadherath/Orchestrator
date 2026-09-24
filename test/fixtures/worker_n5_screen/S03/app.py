import json
import sys


def solve(data):
    totals = {name: row["count"] * row["ms"]
              for name, row in data["stages"].items()}
    largest = max(totals.values())
    bottleneck = min(name for name, total in totals.items() if total == largest)
    return {"bottleneck": bottleneck,
            "contradicts_suspect": bottleneck != data["suspect"]}


if __name__ == "__main__":
    print(json.dumps(solve(json.loads(sys.stdin.readline()))))
