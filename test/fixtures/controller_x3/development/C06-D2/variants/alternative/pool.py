"""Equivalent one-slot reservation with an explicit remaining queue."""


def select(requests, capacity):
    first_foreground = next((row for row in requests
                             if row["kind"] == "foreground"), None)
    ordered = ([first_foreground] if first_foreground is not None else [])
    ordered.extend(row for row in requests if row is not first_foreground)
    return [row["id"] for row in ordered[:capacity]]
