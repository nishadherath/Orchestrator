from delivery import DeliveryStore


class Journal:
    def __init__(self):
        self.deliveries = DeliveryStore()
        self.offsets = {}

    def ingest(self, operation):
        tenant = operation["tenant"]
        partition = operation["partition"]
        offset = operation["offset"]
        stream = (tenant, partition)
        previous = self.offsets.get(stream, -1)
        if offset < previous:
            return {"status": "stale"}
        if offset == previous:
            existing = self.deliveries.lookup(
                tenant, operation["delivery_id"], operation["payload"])
            return existing if existing is not None else {"status": "stale"}
        result = self.deliveries.commit(
            tenant, operation["delivery_id"], operation["payload"],
            operation.get("fail_before_commit", False))
        if result["status"] in {"committed", "replayed"}:
            self.offsets[stream] = offset
        return result
