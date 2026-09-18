from contextlib import closing


def stream_to(response, sink):
    with closing(response):
        for chunk in response.iter_chunks():
            sink.write(chunk)
