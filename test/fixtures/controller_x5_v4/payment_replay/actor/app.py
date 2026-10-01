"""Line-oriented entry point for payment attempts."""
import json
import sys

from payments import process


if __name__ == "__main__":
    print(json.dumps(process(json.loads(sys.stdin.readline())), sort_keys=True))
