# Close streaming resources on every exit

`stream_to` leaks the response when iteration, cancellation, or the output sink
fails. Preserve incremental streaming and propagate the original error while
guaranteeing closure. Change only `downloader/streaming.py`.

Run `python -m unittest discover -s public_checks -v` from the repository root.
