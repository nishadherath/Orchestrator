"""Line-oriented durable customer import adapter."""
import json
import sys

from migration import replay


if __name__ == "__main__":
    print(json.dumps(replay(json.loads(sys.stdin.readline())), sort_keys=True))
