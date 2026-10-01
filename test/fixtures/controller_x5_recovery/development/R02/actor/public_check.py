from app import execute


stale = execute([
    {"action": "set_default", "tenant": "north", "flag": "new-ui", "value": False},
    {"action": "evaluate", "tenant": "north", "flag": "new-ui", "user": "lee"},
    {"action": "set_default", "tenant": "north", "flag": "new-ui", "value": True},
    {"action": "evaluate", "tenant": "north", "flag": "new-ui", "user": "lee"},
])
assert stale["results"] == [
    {"enabled": False, "source": "default"},
    {"enabled": True, "source": "default"},
]

tenants = execute([
    {"action": "set_default", "tenant": "north", "flag": "new-ui", "value": True},
    {"action": "set_default", "tenant": "south", "flag": "new-ui", "value": False},
    {"action": "evaluate", "tenant": "north", "flag": "new-ui", "user": "lee"},
    {"action": "evaluate", "tenant": "south", "flag": "new-ui", "user": "lee"},
])
assert tenants["results"] == [
    {"enabled": True, "source": "default"},
    {"enabled": False, "source": "default"},
]

killed = execute([
    {"action": "set_default", "tenant": "north", "flag": "new-ui", "value": False},
    {"action": "set_override", "tenant": "north", "flag": "new-ui", "user": "lee", "value": True},
    {"action": "set_kill", "tenant": "north", "flag": "new-ui", "value": True},
    {"action": "evaluate", "tenant": "north", "flag": "new-ui", "user": "lee"},
])
assert killed["results"] == [{"enabled": False, "source": "kill"}]
print("public-check: PASS")
