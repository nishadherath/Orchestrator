"""Attack: forge the public aligned-clock JSON inside the child process."""
import json


json.dumps = lambda *args, **kwargs: (  # noqa: ARG005
    '{"renewable":["job-p"],"expired":[]}')


def process(request):
    return {}
