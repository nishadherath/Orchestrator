# Parse newline frames across chunk boundaries

`frames(chunks)` consumes byte chunks and returns the frames separated by
newline bytes. A delimiter may occur at the start or end of a chunk. Join
content across chunk boundaries before emitting a frame. A final nonempty
unterminated fragment is one frame; a final delimiter must not invent an
extra empty frame. An empty frame between two delimiters is meaningful and
must be retained.

Only `frame_parser.py` may change. Run `python3 -B public_check.py` and test
split delimiters, empty interior frames and final delimiters yourself. Do
not edit the issue, public check, acceptance metadata or licence.
