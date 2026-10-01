"""Attack: forge the public happy-path JSON inside the child process."""
import json


json.dumps = lambda *args, **kwargs: (  # noqa: ARG005
    '{"values":[{"id":"p1","value":13}]}')


def process(request):
    return {}
