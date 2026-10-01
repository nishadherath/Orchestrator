"""Useful server-clock repair with an unresolved exact-expiry boundary."""


def process(request):
    renewable, expired = [], []
    for row in request["leases"]:
        (renewable if row["server_now"] <= row["expires_at"] else expired).append(
            row["id"])
    return {"renewable": renewable, "expired": expired}
