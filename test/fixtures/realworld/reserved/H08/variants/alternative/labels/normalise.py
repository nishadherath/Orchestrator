import re
def normalise(value): return re.sub(r"\s+", " ", value).strip()
