class ReportService:
    def __init__(self, loader, cache):
        self._loader = loader
        self._cache = cache

    def get(self, tenant_id, record_id, options=None):
        if record_id not in self._cache:
            self._cache[record_id] = self._loader(tenant_id, record_id, dict(options or {}))
        return self._cache[record_id]
