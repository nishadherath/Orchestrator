"""Actor-visible test of unwanted XDG directory creation."""
import os
from pathlib import Path
from unittest.mock import patch

from platformdirs.unix import Unix


def main() -> None:
    created = []
    with patch.dict(os.environ, {"XDG_DATA_DIRS": "/q3/first:/q3/second"}):
        with patch.object(Path, "mkdir", lambda self, **kwargs: created.append(str(self))):
            value = Unix("demo", ensure_exists=True).site_data_dir
    assert value == "/q3/first/demo"
    assert created == [value]


if __name__ == "__main__":
    main()
