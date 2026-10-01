"""Prioritise every foreground request and accidentally starve retries."""


def select(requests, capacity):
    ordered = ([row for row in requests if row["kind"] == "foreground"]
               + [row for row in requests if row["kind"] == "retry"])
    return [row["id"] for row in ordered[:capacity]]
