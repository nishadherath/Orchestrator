def stream_to(response, sink):
    for chunk in response.iter_chunks():
        sink.write(chunk)
    response.close()
