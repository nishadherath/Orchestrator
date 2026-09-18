def respond(body, etag, if_none_match=None):
    if if_none_match == etag:
        return 304, b"", {"ETag": etag, "Content-Length": "0"}
    return 200, body, {"ETag": etag, "Content-Length": str(len(body))}
