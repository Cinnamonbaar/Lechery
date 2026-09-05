"""Talking to the browser, when there is one.

Shared by everything that puts an element on the page. Every call is
guarded and every failure is a None or a False, because a browser that
declines is a reason to fall back, never a reason to take the game down.
"""

from __future__ import annotations

from typing import Optional

from . import metrics


def window():
    """pygbag's handle on the browser window, or None."""
    try:
        import platform as runtime  # pygbag replaces this with its own

        return getattr(runtime, "window", None)
    except Exception:
        return None


def document():
    handle = window()
    if handle is None:
        return None
    try:
        return handle.document
    except Exception:
        return None


def in_browser() -> bool:
    return document() is not None


def canvas():
    """The canvas pygbag draws into.

    pygbag hangs it off the window, which is more dependable than guessing
    an element id -- the id is a template detail and has changed.
    """
    handle = window()
    if handle is None:
        return None
    try:
        found = getattr(handle, "canvas", None)
        if found is not None:
            return found
        return handle.document.getElementById("canvas")
    except Exception:
        return None


def css_geometry(rect) -> tuple[float, float, float, float]:
    """A device-pixel rect as CSS pixels: (left, top, width, height).

    The one place the two coordinate systems meet. The page lays out in CSS
    pixels while the canvas is drawn at device resolution, so an element
    positioned with raw canvas coordinates lands at scale-times its
    intended place -- off-screen on any phone.

    The scale is read live from the module rather than imported: binding it
    once at import is exactly the bug that put the first overlaid element
    hundreds of pixels below the page.
    """
    scale = metrics.SCALE or 1.0
    return (rect.x / scale, rect.y / scale, rect.width / scale, rect.height / scale)


def call(path: str, *args) -> Optional[object]:
    """Call `window.<path>(*args)`, returning None if anything is missing.

    `path` is dotted, so "LecheryAvatar.place" walks the window. Missing
    objects are the normal case off the web and while a script is still
    loading, so they are not errors.
    """
    target = window()
    if target is None:
        return None
    try:
        for name in path.split("."):
            target = getattr(target, name, None)
            if target is None:
                return None
        return target(*args)
    except Exception:
        return None
