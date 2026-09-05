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


def evaluate(source: str) -> Optional[str]:
    """Run JavaScript in the page and return its result as a string.

    Everything that talks to our own scripts goes through here rather than
    through attribute access on the window proxy. Two things the bridge
    does not reliably do: find globals a page script defined, and marshal a
    Python dict into a JavaScript object. Both fail silently, which is
    indistinguishable from the script never having loaded -- and that is
    exactly the confusion this replaced.

    A string comes back because that always marshals.
    """
    handle = window()
    if handle is None:
        return None
    try:
        result = handle.eval(source)
    except Exception:
        return None
    return "" if result is None else str(result)


def call_json(path: str, payload) -> bool:
    """Call `window.<path>(payload)` with `payload` sent as JSON.

    JSON rather than the object itself: a literal in the source is one
    thing the bridge cannot get wrong.
    """
    import json

    try:
        encoded = json.dumps(payload)
    except (TypeError, ValueError):
        return False
    return evaluate(f"window.{path}({encoded})") is not None


def call(path: str, *args) -> Optional[str]:
    """Call `window.<path>(*args)` with simple scalar arguments."""
    import json

    try:
        rendered = ", ".join(json.dumps(a) for a in args)
    except (TypeError, ValueError):
        return None
    return evaluate(f"window.{path}({rendered})")
