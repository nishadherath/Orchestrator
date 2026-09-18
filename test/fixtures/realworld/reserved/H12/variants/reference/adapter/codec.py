def encode(value, legacy=False):
    if legacy: return b"v1:"+value.encode()
    raw=value.encode(); return f"v2:{len(raw)}|".encode()+raw
def decode(payload):
    if payload.startswith(b"v1:"): return payload[3:].decode()
    header,raw=payload.split(b"|",1)
    if int(header[3:])!=len(raw): raise ValueError("invalid frame length")
    return raw.decode()
