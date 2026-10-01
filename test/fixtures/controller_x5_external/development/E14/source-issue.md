- [x] Initially raised as discussion #3481 

Example Starlette app:

```python
# main.py
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route


async def homepage(request: Request) -> JSONResponse:
    return JSONResponse({"next": str(request.url_for("homepage").include_query_params(a="b", c=["d", "e"]))})


routes = [
    Route("/", endpoint=homepage)
]

app = Starlette(debug=True, routes=routes)
```

When I run this with `uvicorn main:app` and go to http://localhost:8000/ in my browser, I get this output:
```json
{
  "next": "http://localhost:8000/?a=b&c=%5B%27d%27%2C+%27e%27%5D"
}
```

when ideally I would get:
```json
{
  "next": "http://localhost:8000/?a=b&c=d&c=e"
}
```

`starlette.datastructures.URL` does seem to have some support for multi-valued values, but it's `include_query_params` doesn't seem to interrogate the type to check if it's a `list`/`tuple` before stringifying the value.

This is on Starlette main (d9ed5b0f98fdf081fb138473129b72eb035153a3) and `uvicorn==0.52.4`.