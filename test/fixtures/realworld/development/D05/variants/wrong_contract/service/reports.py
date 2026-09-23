class ReportService:
    def __init__(self, loader, cache):
        self._loader = loader
        self._cache = cache

    def get(self, tenant_id, record_id, options=None):
        return self._loader(tenant_id, record_id, dict(options or {}))
