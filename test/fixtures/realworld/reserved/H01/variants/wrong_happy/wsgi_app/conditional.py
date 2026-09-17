def respond(body, etag, if_none_match=None):
    if if_none_match == etag:
        return 304, b"", {}
    return 200, body, {"ETag": etag}
