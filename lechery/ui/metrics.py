"""The scale between design units and screen pixels.

Every size in the interface is authored in *design units* -- roughly CSS
pixels, the size things should physically appear. On a high-density screen
one design unit is several real pixels, and rendering at design units means
the browser upscales the result, which is exactly the blur this avoids.

So the display is created at device resolution and every design size is
multiplied on the way out. `px()` is that multiplication, applied at the
point of use rather than baked into the constants, so the scale can change
when a window moves between displays.

Scale 1.0 is the default and makes this layer invisible, which is what the
desktop and the tests run at.
"""

from __future__ import annotations

#: Current device pixels per design unit.
SCALE = 1.0

#: Below 1 there is nothing to gain, and past 4 the pixel count grows faster
#: than any phone's fill rate is worth.
MIN_SCALE = 1.0
MAX_SCALE = 4.0


def set_scale(value: float) -> float:
    """Set the device pixel ratio. Returns what was actually adopted."""
    global SCALE
    try:
        value = float(value)
    except (TypeError, ValueError):
        return SCALE
    if value <= 0:
        return SCALE
    SCALE = max(MIN_SCALE, min(MAX_SCALE, value))
    return SCALE


def px(value: float) -> int:
    """Design units to device pixels."""
    return int(round(value * SCALE))


def design(value: float) -> float:
    """Device pixels back to design units.

    Layout *decisions* are made in design units -- whether a window is
    phone-shaped is a question about its physical size, not its pixel
    count, and a 1170px-wide phone would otherwise be measured as a
    desktop.
    """
    return value / SCALE


def design_size(size: tuple[int, int]) -> tuple[float, float]:
    return (design(size[0]), design(size[1]))
