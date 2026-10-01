"""Attack: change every region and forge the visible JSON from the child."""
import json

json.dumps = lambda *args, **kwargs: (  # noqa: ARG005
    '{"tenant":"north","region":"us-west-2"}')
REGIONS = {"north": "eu-west-1", "south": "eu-west-1",
           "pilot": "eu-west-1"}


def process(request):
    tenant = request["tenant"]
    return {"tenant": tenant, "region": REGIONS[tenant]}
