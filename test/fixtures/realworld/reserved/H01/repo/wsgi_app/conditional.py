def respond(body, etag, if_none_match=None):
    if if_none_match:
        return 304, body, {"ETag": etag}
    return 200, body, {"ETag": etag, "Content-Length": str(len(body))}
