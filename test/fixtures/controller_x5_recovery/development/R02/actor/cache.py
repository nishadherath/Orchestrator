class DecisionCache:
    def __init__(self):
        self.rows = {}

    def get(self, tenant, flag, user, version):
        return self.rows.get((flag, user))

    def put(self, tenant, flag, user, version, decision):
        self.rows[(flag, user)] = dict(decision)
