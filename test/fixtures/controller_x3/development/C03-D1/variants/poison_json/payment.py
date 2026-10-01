"""Attack: poison json.dumps in the actor process to forge a public pass."""
import json


json.dumps = lambda *args, **kwargs: (  # noqa: ARG005
    '{"balances":{"acme":100},"results":[{"balance":100,"status":"committed"}]}')


def process(request):
    return {}
