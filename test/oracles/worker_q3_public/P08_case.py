"""Hidden side-effect probes with filesystem creation intercepted."""
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

from platformdirs.macos import MacOS
from platformdirs.unix import Unix


def run(row):
    kind = row["kind"]
    created = []
    env = {"XDG_DATA_DIRS": "/q3/first:/q3/second",
           "XDG_CONFIG_DIRS": "/q3/config1:/q3/config2"}
    with patch.dict(os.environ, env):
        with patch.object(Path, "mkdir", lambda self, **kwargs: created.append(str(self))):
            if kind == "xdg-data":
                value = Unix("demo", ensure_exists=True).site_data_dir
            elif kind == "xdg-multi":
                value = Unix("demo", multipath=True, ensure_exists=True).site_data_dir
            elif kind == "xdg-config":
                value = Unix("demo", ensure_exists=True).site_config_dir
            elif kind == "xdg-iterator":
                # Select the site-only iterator regardless of the actor UID.
                with patch.object(Unix, "_use_site", True):
                    value = next(Unix("demo", ensure_exists=True).iter_data_dirs())
            elif kind == "unix-path":
                with patch.dict(os.environ, {"XDG_DATA_DIRS": ""}):
                    value = str(Unix("demo", ensure_exists=True).site_data_path)
            elif kind == "mac-cache":
                with patch.object(sys, "base_prefix", "/q3/opt/python"):
                    value = MacOS("demo", ensure_exists=True).site_cache_dir
            elif kind == "mac-cache-path":
                with patch.object(sys, "base_prefix", "/q3/opt/python"):
                    value = str(MacOS("demo", multipath=True, ensure_exists=True).site_cache_path)
            elif kind == "disabled":
                value = Unix("demo", ensure_exists=False).site_data_dir
            else:
                raise ValueError(kind)
    return [value, created]


print(json.dumps(run(json.loads(sys.stdin.read())), sort_keys=True))
