from __future__ import annotations

import json


class ReportService:
    def __init__(self, loader, cache):
        self._loader = loader
        self._cache = cache

    def get(self, tenant_id: str, record_id: int, options: dict | None = None):
        supplied = dict(options or {})
        key = json.dumps([tenant_id, record_id, supplied], sort_keys=True, separators=(",", ":"))
        try:
            return self._cache[key]
        except KeyError:
            value = self._loader(tenant_id, record_id, supplied)
            self._cache[key] = value
            return value
