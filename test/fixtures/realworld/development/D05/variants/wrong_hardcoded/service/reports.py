class ReportService:
    def __init__(self, loader, cache):
        self._loader = loader
        self._cache = cache

    def get(self, tenant_id, record_id, options=None):
        key = (tenant_id, record_id)
        if key not in self._cache:
            self._cache[key] = self._loader(tenant_id, record_id, dict(options or {}))
        return self._cache[key]
