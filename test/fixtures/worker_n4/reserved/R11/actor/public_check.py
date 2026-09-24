from app import solve
assert solve({'actual_upstream': 'east', 'expected_upstream': 'west'}) == {'action': 'no-code-change', 'cause': 'upstream-config', 'observed': 'east'}
