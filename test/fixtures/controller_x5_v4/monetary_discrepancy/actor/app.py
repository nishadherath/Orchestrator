import json
import sys
from amounts import reconcile
if __name__=="__main__":
    print(json.dumps(reconcile(json.loads(sys.stdin.readline())),sort_keys=True))
