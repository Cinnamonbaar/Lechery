"""A real HTML input, overlaid on the canvas where a text field is drawn.

A canvas cannot open a phone's keyboard. Safari only raises it for a
focused HTML input, and calling focus() from our frame loop does not count
as a user gesture, so asking for the keyboard programmatically fails
silently -- which is exactly the "I tap the field and nothing happens"
symptom.

So the field is not asked to summon a keyboard: a real input element is
positioned over the place the field is drawn, and the player taps *that*.
The gesture lands on a genuine input, iOS opens the keyboard because it
always would, and no permission question arises. It also brings selection,
autocorrect, and IME along for free -- all things a hand-rolled text field
in a canvas spends years failing to reproduce.

Outside a browser none of this exists and the field falls back to reading
pygame key events.
"""

from __future__ import annotations

from typing import Optional

# The module, not the value: `from .metrics import SCALE` binds whatever
# the scale was at import time, and set_scale would never be seen here --
# which put this element at three times its coordinates on a phone, off the
# bottom of the page where nothing could tap it.
from . import metrics

#: iOS zooms the page whenever a focused input's text is smaller than this,
#: then scrolls the field into view -- which reads as the screen lurching
#: and zooming the moment you tap. Staying at or above it is the only way
#: to decline, short of disabling zoom for the whole page.
MIN_FONT_PX = 16

#: Serial number for element ids. Focus is compared by id rather than by
#: object identity: the browser bridge returns a fresh proxy object on
#: every attribute access, so two proxies for the same element are never
#: `is`-identical and an identity check silently always says "not focused".
_NEXT_ID = 0


#: Every input currently on the page. Kept so the frame loop can ask
#: whether one is focused: a phone keyboard opening shrinks the viewport,
#: and resizing the display in response destroys the focus that opened it.
_LIVE: list["NativeInput"] = []


#: Above the canvas, whatever it claims for itself. SDL styles the canvas
#: without asking, so competing politely here just loses the tap.
Z_INDEX = 2147483000


def browser_window():
    """pygbag's handle on the browser window, or None."""
    try:
        import platform as runtime  # pygbag replaces this with its own

        return getattr(runtime, "window", None)
    except Exception:
        return None


def browser_document():
    """The page's document, or None when not running in a browser."""
    window = browser_window()
    if window is None:
        return None
    try:
        return window.document
    except Exception:
        return None


def game_canvas():
    """The canvas pygbag is drawing into.

    pygbag hangs it off the window directly, which is more dependable than
    guessing an element id -- the id is a template detail and has changed.
    """
    window = browser_window()
    if window is None:
        return None
    try:
        canvas = getattr(window, "canvas", None)
        if canvas is not None:
            return canvas
        return window.document.getElementById("canvas")
    except Exception:
        return None


def any_focused() -> bool:
    """Whether the player is typing into any overlaid field."""
    return any(field.focused for field in _LIVE)


def any_present() -> bool:
    """Whether any overlaid field exists at all.

    Used as the safety net behind `any_focused`: focus detection depends on
    the browser bridge behaving, and it is precisely the thing that failed
    here, so the viewport rules do not rest on it alone.
    """
    return bool(_LIVE)


def ask_text(prompt: str, initial: str = "") -> Optional[str]:
    """Ask for a line of text with the browser's own dialog.

    The fallback for when the overlaid input does not receive the tap. It
    is uglier than an inline field and it blocks the frame, but a native
    dialog raises the keyboard on every platform without depending on
    stacking order or event routing -- so it works exactly in the case
    where the nicer path has failed.
    """
    window = browser_window()
    if window is None:
        return None
    try:
        result = window.prompt(prompt, initial)
    except Exception:
        return None
    return None if result is None else str(result)


def available() -> bool:
    return browser_document() is not None


def css_geometry(rect) -> tuple[float, float, float, float]:
    """A device-pixel rect as CSS pixels: (left, top, width, height).

    The one place the two coordinate systems meet. The page lays out in CSS
    pixels while the canvas is drawn at device resolution, so an element
    positioned with raw canvas coordinates lands at scale-times its
    intended place -- off-screen on any phone.
    """
    scale = metrics.SCALE or 1.0
    return (rect.x / scale, rect.y / scale, rect.width / scale, rect.height / scale)


class NativeInput:
    """An <input> element tracking one on-canvas text field."""

    #: This element's DOM id, unique per instance.
    element_id: str = ""

    def __init__(
        self,
        rect,
        *,
        text: str = "",
        max_length: int = 40,
        placeholder: str = "",
        colour: str = "#cec8c4",
        font_size: int = 15,
    ) -> None:
        self.element = None
        self._rect = None

        document = browser_document()
        if document is None:
            return

        global _NEXT_ID
        _NEXT_ID += 1
        self.element_id = f"lechery-field-{_NEXT_ID}"

        try:
            element = document.createElement("input")
            element.id = self.element_id
            element.type = "text"
            element.value = text
            element.maxLength = max_length
            element.placeholder = placeholder
            element.autocomplete = "off"
            element.autocapitalize = "words"
            element.spellcheck = False

            style = element.style
            style.position = "fixed"
            style.zIndex = str(Z_INDEX)
            # Made visible rather than transparent: an invisible element
            # that is not receiving taps is indistinguishable from one that
            # was never created, and this has to be diagnosable from a
            # screenshot.
            style.background = "#1a171f"
            style.border = "1px solid #3a3442"
            style.borderRadius = "4px"
            style.outline = "none"
            # Both are needed on iOS: without them the element can be
            # painted above the canvas and still route its taps below.
            style.pointerEvents = "auto"
            style.touchAction = "manipulation"
            style.webkitUserSelect = "text"
            style.color = colour
            style.caretColor = "#dec088"
            style.fontFamily = "Georgia, serif"
            style.fontSize = f"{max(font_size, MIN_FONT_PX)}px"
            style.padding = "0 10px"
            style.margin = "0"

            document.body.appendChild(element)
            self.element = element
            _LIVE.append(self)
            self.move(rect)
        except Exception:
            # A browser that will not have it is not worth crashing over;
            # the canvas field still works with a hardware keyboard.
            self.element = None

    # -- geometry ---------------------------------------------------------

    def move(self, rect) -> None:
        """Place the element over `rect`, which is in device pixels."""
        if self.element is None or rect == self._rect:
            return
        self._rect = rect
        left, top, width, height = css_geometry(rect)
        try:
            style = self.element.style
            style.left = f"{left:.1f}px"
            style.top = f"{top:.1f}px"
            style.width = f"{width:.1f}px"
            style.height = f"{height:.1f}px"
        except Exception:
            pass

    # -- content ----------------------------------------------------------

    @property
    def value(self) -> str:
        if self.element is None:
            return ""
        try:
            return str(self.element.value)
        except Exception:
            return ""

    @property
    def focused(self) -> bool:
        """Whether this element currently has focus.

        Compared by id, not by identity: the bridge returns a new proxy for
        every attribute access, so `document.activeElement is self.element`
        is False even while the element is focused -- which made the frame
        loop resize the display out from under the keyboard.
        """
        document = browser_document()
        if self.element is None or document is None:
            return False
        try:
            active = document.activeElement
            if active is None:
                return False
            return str(active.id) == self.element_id
        except Exception:
            return False

    def destroy(self) -> None:
        """Remove the element. Leaking these leaves invisible inputs on the
        page that keep catching taps meant for the game."""
        if self in _LIVE:
            _LIVE.remove(self)
        if self.element is None:
            return
        try:
            self.element.remove()
        except Exception:
            pass
        self.element = None
