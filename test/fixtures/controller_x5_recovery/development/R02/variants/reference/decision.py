def decide(context):
    if context["killed"]:
        return {"enabled": False, "source": "kill"}
    if context["override"] is not None:
        return {"enabled": context["override"], "source": "override"}
    if context["default"] is not None:
        return {"enabled": context["default"], "source": "default"}
    return {"enabled": False, "source": "missing"}
