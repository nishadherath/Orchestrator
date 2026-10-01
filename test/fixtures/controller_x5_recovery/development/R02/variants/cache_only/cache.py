class DecisionCache:
    def __init__(self):
        self.rows = {}

    def get(self, tenant, flag, user, version):
        value = self.rows.get((tenant, flag, user, version))
        return dict(value) if value is not None else None

    def put(self, tenant, flag, user, version, decision):
        self.rows[(tenant, flag, user, version)] = dict(decision)
