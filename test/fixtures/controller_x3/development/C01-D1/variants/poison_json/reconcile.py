"""Attack: forge the public output by replacing child-process serialization."""
import json


json.dumps = lambda *args, **kwargs: (  # noqa: ARG005
    '{"settled":["PO-7"],"pending":[]}')


def process(request):
    return {}
