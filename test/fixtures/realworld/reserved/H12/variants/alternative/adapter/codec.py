def encode(value, legacy=False):
    raw=value.encode()
    return b"v1:"+raw if legacy else b"v2:"+str(len(raw)).encode()+b"|"+raw
def decode(payload):
    prefix,payload=payload[:3],payload[3:]
    if prefix==b"v1:": return payload.decode()
    if prefix!=b"v2:": raise ValueError("unknown format")
    size,raw=payload.split(b"|",1)
    if len(raw)!=int(size): raise ValueError("invalid frame length")
    return raw.decode()
