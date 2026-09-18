def encode(value, legacy=False):
    raw=value.encode(); return f"v2:{len(raw)}|".encode()+raw
def decode(payload): return payload.split(b"|",1)[-1].decode()
