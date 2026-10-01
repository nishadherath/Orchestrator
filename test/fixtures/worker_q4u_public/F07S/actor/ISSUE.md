# Escape event references consistently

An event reference is a sequence of text components joined by `|`. A literal
`|` inside a component must be encoded as `\|`, and a literal backslash as
`\\`. Decode these escapes back to the original components. A trailing
unpaired escape is invalid and must raise `ValueError`. Ordinary components
without reserved characters must keep their existing representation.

Fix `event_ref/encode.py` and `event_ref/decode.py` as needed. Run
`python3 -B public_check.py`; add your own cases for literal delimiters,
backslashes and malformed trailing escapes. Do not edit the issue, public
check, acceptance metadata or licence.
