"""Independent loop implementation of the exclusive count bound."""


def process(request):
    selected = []
    for index, item in enumerate(request["items"]):
        if index >= request["limit"]:
            break
        selected.append(item)
    return {"selected": selected}
