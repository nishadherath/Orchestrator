import json, sys

def solve(data):
    actual = data['actual_upstream']
    if actual != data['expected_upstream']:
        return {'action': 'no-code-change', 'cause': 'upstream-config', 'observed': actual}
    return {'action': 'investigate-code', 'cause': 'undetermined', 'observed': actual}

if __name__ == '__main__':
    print(json.dumps(solve(json.loads(sys.stdin.readline()))))
