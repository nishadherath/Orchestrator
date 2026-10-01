"""Faulty baseline: worker-local time decides server lease expiry."""


def process(request):
    renewable, expired = [], []
    for row in request["leases"]:
        (renewable if row["worker_now"] < row["expires_at"] else expired).append(
            row["id"])
    return {"renewable": renewable, "expired": expired}
