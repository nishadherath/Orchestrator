"""Cache report rows from an injected loader."""
from __future__ import annotations


class ReportService:
    def __init__(self, loader, cache):
        self._loader = loader
        self._cache = cache

    def get(self, tenant_id: str, record_id: int, options: dict | None = None):
        key = record_id
        if key not in self._cache:
            self._cache[key] = self._loader(tenant_id, record_id, dict(options or {}))
        return self._cache[key]
