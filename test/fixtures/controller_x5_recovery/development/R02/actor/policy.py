class PolicyStore:
    def __init__(self):
        self.defaults = {}
        self.overrides = {}
        self.kills = {}
        self.versions = {}

    def apply(self, operation):
        tenant = operation["tenant"]
        flag = operation["flag"]
        key = (tenant, flag)
        action = operation["action"]
        if action == "set_default":
            self.defaults[key] = operation["value"]
        elif action == "set_override":
            self.overrides[(tenant, flag, operation["user"])] = operation["value"]
        elif action == "set_kill":
            self.kills[key] = operation["value"]
        else:
            raise ValueError("unknown policy action")
        self.versions[key] = self.versions.get(key, 0) + 1

    def context(self, tenant, flag, user):
        key = (tenant, flag)
        return {
            "default": self.defaults.get(key),
            "override": self.overrides.get((tenant, flag, user)),
            "killed": self.kills.get(key, False),
            "version": self.versions.get(key, 0),
        }
