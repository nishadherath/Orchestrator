"""Line-oriented order fulfilment adapter."""
import json
import sys

from shipments import process


if __name__ == "__main__":
    print(json.dumps(process(json.loads(sys.stdin.readline())), sort_keys=True))
