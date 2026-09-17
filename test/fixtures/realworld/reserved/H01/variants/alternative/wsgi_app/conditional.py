def respond(body, etag, if_none_match=None):
    matched = if_none_match is not None and if_none_match == etag
    payload = b"" if matched else body
    return (304 if matched else 200), payload, {
        "ETag": etag,
        "Content-Length": str(len(payload)),
    }
