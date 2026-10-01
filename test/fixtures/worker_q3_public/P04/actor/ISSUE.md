# Explicit port zero is lost across urllib3 components

An integration using port zero as an explicit endpoint value finds that URL
rendering, host comparison, pool lookup and proxy construction disagree about
the selected port. `None` means unspecified and should still select the usual
scheme default. An explicit integer zero must remain zero throughout those
operations. Preserve ordinary ports, host comparisons and parsing behaviour.

Run `python3 -B public_check.py` for an offline smoke check. Edit only
`urllib3/connectionpool.py`, `urllib3/poolmanager.py` and
`urllib3/util/url.py`. The evaluation also checks combinations beyond the
smoke check. Do not edit tests, issue, acceptance file or licence.
