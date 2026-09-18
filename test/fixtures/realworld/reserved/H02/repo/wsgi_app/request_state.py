_current = None


def current_metadata():
    return _current


def run_request(metadata, work):
    global _current
    _current = metadata
    return work()
