"""Public smoke check for a single complete chunk."""
from frame_parser import frames


assert frames([b"first\nsecond"]) == [b"first", b"second"]
