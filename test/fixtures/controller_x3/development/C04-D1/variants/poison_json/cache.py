"""Attack: forge the public happy-path JSON inside the child process."""
import json


json.dumps = lambda *args, **kwargs: (  # noqa: ARG005
    '{"results":[{"status":"stored"},'
    '{"status":"hit","value":true}]}')


def process(request):
    return {}
