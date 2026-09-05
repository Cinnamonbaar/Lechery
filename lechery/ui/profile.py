"""Choosing a screen layout from the window, not from the device.

Device detection is the obvious approach and the wrong one: it is
unreliable, untestable, and answers the wrong question. A desktop window
dragged narrow needs the compact layout; a tablet in landscape does not.
Both are settled correctly by measuring the window, which also means every
layout decision here is testable without owning the hardware.
"""

from __future__ import annotations

from enum import Enum

from ..settings import LayoutMode
from .metrics import design_size


class FormFactor(Enum):
    #: Three panes side by side.
    WIDE = "wide"
    #: One pane at a time, bars overlaying as drawers.
    COMPACT = "compact"


#: Below this width there is not enough room for two bars and a play area.
MIN_WIDE_WIDTH = 900

#: A window taller than it is wide is a phone held upright, or a desktop
#: window someone has made that shape deliberately. Either way, side-by-side
#: panes would leave the world a letterbox.
PORTRAIT_RATIO = 1.15


def measure(window: tuple[int, int]) -> FormFactor:
    """The form factor a window of this size wants.

    Measured in design units, not pixels: whether a screen is phone-shaped
    is a question about its physical size. A 1170-pixel-wide phone would
    otherwise be mistaken for a desktop.
    """
    width, height = design_size(window)
    if width < MIN_WIDE_WIDTH:
        return FormFactor.COMPACT
    if width / max(height, 1) < PORTRAIT_RATIO:
        return FormFactor.COMPACT
    return FormFactor.WIDE


def resolve(mode: LayoutMode, window: tuple[int, int]) -> FormFactor:
    """Apply the player's setting over the measurement.

    An explicit choice always wins, including when it is the awkward one --
    someone who picks WIDE on a phone has said what they want, and second
    guessing a stated preference is worse than an ugly screen.
    """
    if mode is LayoutMode.WIDE:
        return FormFactor.WIDE
    if mode is LayoutMode.COMPACT:
        return FormFactor.COMPACT
    return measure(window)
