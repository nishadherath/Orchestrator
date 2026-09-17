# Honour conditional response validators after content changes

Return 304 with an empty body only when `If-None-Match` equals the current ETag.
Otherwise return the current body and complete response headers. Change only
`wsgi_app/conditional.py`.
