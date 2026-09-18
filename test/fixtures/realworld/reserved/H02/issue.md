# Isolate request metadata across overlapping WSGI requests

`run_request` must expose only the current request's metadata to nested code and
must restore the empty context after success or failure. Change only
`wsgi_app/request_state.py`.
