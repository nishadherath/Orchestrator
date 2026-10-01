"""Deployed region map; a new target needs operator approval."""
REGIONS = {"north": "us-west-2", "south": "eu-central-1",
           "pilot": "us-west-2"}


def process(request):
    tenant = request["tenant"]
    return {"tenant": tenant, "region": REGIONS[tenant]}
