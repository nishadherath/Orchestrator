import json
import sys
from features import run
if __name__=="__main__":
    print(json.dumps(run(json.loads(sys.stdin.readline())),sort_keys=True))
