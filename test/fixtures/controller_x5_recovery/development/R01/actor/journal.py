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
        if offset <= self.offsets.get(stream, -1):
            return {"status": "stale"}
        self.offsets[stream] = offset
        return self.deliveries.commit(
            tenant, operation["delivery_id"], operation["payload"],
            operation.get("fail_before_commit", False))
