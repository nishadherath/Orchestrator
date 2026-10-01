from app import execute


def item(tenant, partition, offset, delivery_id, units, **extra):
    return {"tenant": tenant, "partition": partition, "offset": offset,
            "delivery_id": delivery_id, "payload": {"units": units}, **extra}


replayed = execute([
    item("north", "orders", 4, "evt-4", 7),
    item("north", "orders", 4, "evt-4", 7),
])
assert [row["status"] for row in replayed["results"]] == ["committed", "replayed"]
assert replayed["results"][1]["receipt"] == replayed["results"][0]["receipt"]
assert replayed["totals"] == {"north": 7}

retry = execute([
    item("west", "orders", 8, "evt-9", 4, fail_before_commit=True),
    item("west", "orders", 8, "evt-9", 4),
])
assert [row["status"] for row in retry["results"]] == ["retryable", "committed"]
assert retry["totals"] == {"west": 4}

tenants = execute([
    item("north", "orders", 4, "shared", 3),
    item("south", "orders", 4, "shared", 3),
])
assert [row["status"] for row in tenants["results"]] == ["committed", "committed"]
assert tenants["totals"] == {"north": 3, "south": 3}
print("public-check: PASS")
