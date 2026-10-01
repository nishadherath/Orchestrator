"""Independently classify server-time expiry using a status pass."""


def process(request):
    decisions = [(row["id"], row["expires_at"] - row["server_now"])
                 for row in request["leases"]]
    return {"renewable": [name for name, remaining in decisions if remaining > 0],
            "expired": [name for name, remaining in decisions if remaining <= 0]}
