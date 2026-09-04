"""Where we are running, and what that changes.

Under pygbag the game is a WASM build inside a browser tab, which differs
from a desktop in ways that reach the code: the filesystem is virtual, the
home directory is not a real place, and the frame must be handed back to the
browser or the tab freezes.

Everything here is a question with a cheap answer, so callers can ask
per-call rather than caching a flag at import time -- which also makes it
trivial to fake in a test.
"""

from __future__ import annotations

import sys
from pathlib import Path

#: pygbag builds run under Emscripten, which reports itself in sys.platform.
#: This is the check the pygame ecosystem standardised on.
IS_WEB = sys.platform == "emscripten"


def is_web() -> bool:
    return sys.platform == "emscripten"


def data_dir(app_name: str = "lechery") -> Path:
    """Where to keep settings and saves.

    In the browser there is no home directory. pygbag mounts a persistent
    filesystem at /data, so writes there survive a reload; writes anywhere
    else do not, and fail silently, which is the worse outcome.
    """
    if is_web():
        return Path("/data") / app_name
    return Path.home() / f".{app_name}"
