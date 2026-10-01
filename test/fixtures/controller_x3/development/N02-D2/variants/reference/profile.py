"""Guard absent profile and email values in the local adapter."""


def process(request):
    profile = request.get("profile")
    return {"email": profile.get("email") if isinstance(profile, dict) else None}
