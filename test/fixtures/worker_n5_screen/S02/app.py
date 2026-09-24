import json
import sys


def solve(data):
    return {"stock": data["stock"], "error": None}


if __name__ == "__main__":
    print(json.dumps(solve(json.loads(sys.stdin.readline()))))
