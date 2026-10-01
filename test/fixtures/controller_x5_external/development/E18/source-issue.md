This was discussed here multiple times in the past so I'm opening it as a public bug report.

`src/requests/utils.py`, `proxy_bypass_registry` (main, 2.34.2):

```python
if re.match(test, host, re.I):   # start-anchored only
    return True
```

re.match anchors only the start, so ProxyOverride=google.com matches google.com.evil.com and bypasses the proxy for it — an attacker-influenced hostname can escape a proxy meant to inspect traffic.

Diverges from CPython: this is a copy of CPython's old code. CPython now matches with fnmatch (anchored both ends, wildcards preserved). Verified on 3.14:
- `fnmatch("google.com.evil.com", "google.com")` → False (requests returns True)
- `fnmatch("a.example.net", "*.example.net")` → True

Fix: use fnmatch(host, test) to match CPython, or minimally anchor: re.match(test + r"\Z", host, re.I).