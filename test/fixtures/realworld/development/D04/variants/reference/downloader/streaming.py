def stream_to(response, sink):
    try:
        for chunk in response.iter_chunks():
            sink.write(chunk)
    finally:
        response.close()
