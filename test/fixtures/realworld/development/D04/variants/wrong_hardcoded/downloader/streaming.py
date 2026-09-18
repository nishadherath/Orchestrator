def stream_to(response, sink):
    try:
        sink.write(b"".join(response.iter_chunks()))
    finally:
        response.close()
