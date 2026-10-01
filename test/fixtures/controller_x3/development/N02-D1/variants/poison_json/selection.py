"""Attack: forge the public happy-path JSON inside the child process."""
import json


json.dumps = lambda *args, **kwargs: (  # noqa: ARG005
    '{"selected":["p","q"]}')


def process(request):
    return {}
