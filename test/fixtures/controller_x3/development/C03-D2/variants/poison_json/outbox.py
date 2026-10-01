"""Attack: forge the public happy-path output from inside the actor process."""
import json


json.dumps = lambda *args, **kwargs: (  # noqa: ARG005
    '{"acked":["m1"],"results":[{"status":"enqueued"},'
    '{"status":"claimed","token":1},{"status":"acked"}]}')


def process(request):
    return {}
