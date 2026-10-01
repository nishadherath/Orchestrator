"""Reserve one foreground slot, then honour original arrival order."""


def select(requests, capacity):
    foreground = next((row["id"] for row in requests
                       if row["kind"] == "foreground"), None)
    admitted = [foreground] if foreground is not None and capacity else []
    for row in requests:
        if len(admitted) == capacity:
            break
        if row["id"] not in admitted:
            admitted.append(row["id"])
    return admitted
