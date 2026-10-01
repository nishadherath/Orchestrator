import hashlib
import json


def fingerprint(payload):
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class DeliveryStore:
    def __init__(self):
        self.records = {}
        self.totals = {}

    def lookup(self, tenant, delivery_id, payload):
        record = self.records.get(delivery_id)
        if record is None:
            return None
        if record["fingerprint"] != fingerprint(payload):
            return {"status": "conflict"}
        return {"status": "replayed", "receipt": dict(record["receipt"])}

    def commit(self, tenant, delivery_id, payload, fail_before_commit=False):
        existing = self.lookup(tenant, delivery_id, payload)
        if existing is not None:
            return existing
        if fail_before_commit:
            return {"status": "retryable"}
        total = self.totals.get(tenant, 0) + payload["units"]
        self.totals[tenant] = total
        receipt = {"tenant": tenant, "delivery_id": delivery_id,
                   "units": payload["units"], "total": total}
        self.records[delivery_id] = {"fingerprint": fingerprint(payload),
                                     "receipt": receipt}
        return {"status": "committed", "receipt": dict(receipt)}
