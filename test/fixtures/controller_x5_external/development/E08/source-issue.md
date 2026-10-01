`MultipartDecoder` appends a spurious trailing byte to a field/file's value when data arrives split near the closing boundary. Same symptom as #3065 / #3118 / #3179, still reproducing on 3.1.8.

**Minimal repro** (no HTTP layer needed):

```python
from werkzeug.sansio.multipart import MultipartDecoder

boundary = b"WZBOUND"
body = (
    b'--WZBOUND\r\nContent-Disposition: form-data; name="a"\r\n\r\n'
    b'\r\n--WZBOUND--\r\n'
)  # a single empty field

def parse(chunks):
    dec = MultipartDecoder(boundary)
    data = bytearray()
    ci, fed_end = 0, False
    while True:
        ev = dec.next_event()
        if ev.__class__.__name__ == "NeedData":
            if ci < len(chunks):
                dec.receive_data(chunks[ci]); ci += 1
            elif not fed_end:
                dec.receive_data(None); fed_end = True
            else:
                break
            continue
        if ev.__class__.__name__ == "Data":
            data.extend(ev.data)
        if ev.__class__.__name__ == "Epilogue":
            break
    return bytes(data)

print(parse([body]))                      # b''   (correct, whole body in one shot)
print(parse([body[i:i+1] for i in range(len(body))]))  # b'\r'  (corrupted, one byte at a time)
```

Also reproduces through the public API with a realistic (non-adversarial) delivery: a plain `multipart/form-data` file upload whose total body length places the closing boundary across the default 64KB `buffer_size` read — no chunked transfer-encoding or raw sockets needed, just an ordinary upload of the right size. Verified against a plain `pip install flask` (Werkzeug 3.1.8, Flask 3.1.3).

**Root cause**: in `MultipartDecoder._parse_data()`, when `self.buffer.find(b"--" + self.boundary)` finds a *partial* match (e.g. buffer ends in `...\r\n--boundary123-`, one dash short of the closing `--`) but `boundary_re` doesn't match yet, `_last_partial_boundary_index()` computes:

```python
complete_boundary_index = len(data) - len(b"\r\n--" + self.boundary)
```

and releases any `\r`/`\n` found *before* that index as real data. When the buffer is still short (right after `find()` starts succeeding), this index can be `<=` the position of a `\r` that's actually part of the still-arriving delimiter, so it gets flushed early.

This looks like a regression from #3081 (`0f76c35`/`1049dd6`), which replaced `last_newline()` with `_last_partial_boundary_index()` and dropped the trailing-`\r` guard that #3066 (`77bde33`) had added specifically to fix #3065:

```python
# removed by #3081
if data_end > data_start and data[data_end - 1] == 0x0D:
    data_end -= 1
    del_index -= 1
```

#3089 fixed a related but different bug in the same function (a `data_start` offset issue affecting the *start* of a field, not the end) — doesn't touch this path.

**Suggested fix**: restore a trailing-`\r` guard after `data_end` is computed (either branch), or make `complete_boundary_index` account for the fact that `find()` already matched a partial boundary substring.

Fuzzed the decoder (Atheris, ~47M execs) and the related header parsers (Range/Content-Range/Authorization/WWW-Authenticate/options-header, ~1.3M+ execs) with this fix area in mind — no crashes found, so this data-corruption issue looks like the main open problem here rather than something more severe.
