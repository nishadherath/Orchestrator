import json
import sys


def solve(data):
    return {"port": None, "error": None}


if __name__ == "__main__":
    print(json.dumps(solve(json.loads(sys.stdin.readline()))))
