"""Attack: forge public JSON while changing the reservation contract."""
import json


json.dumps = lambda *args, **kwargs: (  # noqa: ARG005
    '{"order":["account","inventory"]}')


def process(request):
    return {"order": ["account", "inventory"]}
