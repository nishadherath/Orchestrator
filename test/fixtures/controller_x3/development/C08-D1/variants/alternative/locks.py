"""Current caller-visible lock order; the shared-path conflict is unresolved."""


def process(request):
    if request["caller"] == "settlement":
        return {"order": ["account", "inventory"]}
    return {"order": ["inventory", "account"]}
