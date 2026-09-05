"""Loading fonts in a way that survives the browser.

`pygame.font.SysFont` asks the operating system for a font by name. In a
WASM build there is no operating system to ask, so it silently falls back to
a default -- meaning a desktop build and a web build render differently, and
the bug only shows up after packaging. Bundling the typeface and loading it
by path is the fix.

`pygame.font.Font(None, size)` is the safety net: pygame ships its own font
inside the wheel, so it is always available, on every platform.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pygame

from ..platform import is_web
from .metrics import px

#: Drop .ttf files here and name them below to use real typography. The
#: game runs without them; it just looks more generic.
FONT_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "fonts"

#: Role -> bundled filename. Absent files fall through to the next option.
BUNDLED = {
    "body": "body.ttf",
    "heading": "heading.ttf",
}

#: Only consulted on desktop, where an OS font is a real improvement over
#: pygame's default. Never reached in a web build.
SYSTEM_FALLBACK = "georgia,times new roman,serif"

_cache: dict[tuple[str, int, bool], pygame.font.Font] = {}


def load(role: str, size: int, bold: bool = False) -> pygame.font.Font:
    """A font for `role`, cached.

    Tries every source before giving up, and gives up loudly. A font that
    silently fails to load takes the whole interface with it, and in a
    browser that shows up as a blank canvas with no explanation -- so the
    last resort is an exception carrying the reason, not a None that
    crashes somewhere less informative.
    """
    key = (role, size, bold)
    cached = _cache.get(key)
    if cached is not None:
        return cached

    size = px(size)  # design units in, device pixels out
    for source in _sources(role, size, bold):
        font = source()
        if font is not None:
            if bold:
                font.set_bold(True)
            _cache[key] = font
            return font

    raise RuntimeError(
        f"no font available for {role!r} at {size}px: no bundled file, "
        f"no system font, and pygame's own default font failed to load"
    )


def _sources(role: str, size: int, bold: bool):
    """Font sources to try, best first.

    The order differs by platform. On a desktop an OS font is a real
    improvement over pygame's default, so it comes first. In a browser
    there is no OS font list, so pygame's bundled default leads and
    SysFont is only a last resort -- it will almost certainly fail there,
    but a failing last resort is better than no last resort.
    """
    def bundled():
        return _bundled(role, size)

    def default():
        return _default(size)

    def system():
        return _system(size, bold)

    if is_web():
        return (bundled, default, system)
    return (bundled, system, default)


def _default(size: int) -> Optional[pygame.font.Font]:
    """pygame's own font, shipped inside the wheel."""
    try:
        return pygame.font.Font(None, size)
    except (OSError, pygame.error):
        return None


def _bundled(role: str, size: int) -> Optional[pygame.font.Font]:
    name = BUNDLED.get(role)
    if name is None:
        return None
    path = FONT_DIR / name
    if not path.exists():
        return None
    try:
        return pygame.font.Font(str(path), size)
    except (OSError, pygame.error):
        return None


def _system(size: int, bold: bool) -> Optional[pygame.font.Font]:
    try:
        return pygame.font.SysFont(SYSTEM_FALLBACK, size, bold=bold)
    except (OSError, pygame.error):
        return None


def clear_cache() -> None:
    _cache.clear()
