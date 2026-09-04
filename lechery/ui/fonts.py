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
    """A font for `role`, cached. Never raises; always returns something."""
    key = (role, size, bold)
    cached = _cache.get(key)
    if cached is not None:
        return cached

    font = _bundled(role, size) or _system(size, bold) or pygame.font.Font(None, size)
    if bold:
        font.set_bold(True)
    _cache[key] = font
    return font


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
    from ..platform import is_web

    if is_web():
        return None  # there is no system to ask
    try:
        return pygame.font.SysFont(SYSTEM_FALLBACK, size, bold=bold)
    except (OSError, pygame.error):
        return None


def clear_cache() -> None:
    _cache.clear()
