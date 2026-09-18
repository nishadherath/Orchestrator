def encode(value, legacy=False): return ("v1:" if legacy else "v2:")+value
def decode(payload): return payload.split(":",1)[1]
