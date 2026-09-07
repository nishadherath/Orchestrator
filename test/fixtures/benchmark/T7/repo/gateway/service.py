"""Gateway service: routes an incoming request and returns a small routing
acknowledgement. Does not touch the request body itself."""
from shared.serialize import to_wire


def handle_request(n=1):
    """n is accepted for a uniform interface with the other services; the
    ack payload does not depend on it."""
    ack = {"routed": True, "target": "catalogue", "request_id": "r-0001"}
    return to_wire(ack)
