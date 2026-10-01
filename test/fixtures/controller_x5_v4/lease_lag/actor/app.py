import json
import sys
from leases import run
if __name__=="__main__":
    print(json.dumps(run(json.loads(sys.stdin.readline())),sort_keys=True))
