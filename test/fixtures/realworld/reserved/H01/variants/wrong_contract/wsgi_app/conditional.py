def respond(body, etag, if_none_match=None):
    return (304 if if_none_match == etag else 200), body, {"ETag": etag, "Content-Length": str(len(body))}
