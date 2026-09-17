def stream_to(response, sink):
    try:
        for chunk in response.iter_chunks():
            sink.write(chunk)
    except Exception:
        return False
    finally:
        response.close()
    return True
