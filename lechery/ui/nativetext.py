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

from .metrics import SCALE

#: Sits above the canvas. The canvas draws the field's frame underneath.
Z_INDEX = 10


def browser_document():
    """The page's document, or None when not running in a browser."""
    try:
        import platform as runtime  # pygbag replaces this with its own

        window = getattr(runtime, "window", None)
        if window is None:
            return None
        return window.document
    except Exception:
        return None


def available() -> bool:
    return browser_document() is not None


class NativeInput:
    """An <input> element tracking one on-canvas text field."""

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

        try:
            element = document.createElement("input")
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
            style.background = "transparent"
            style.border = "0"
            style.outline = "none"
            style.color = colour
            style.caretColor = "#dec088"
            style.fontFamily = "Georgia, serif"
            style.fontSize = f"{font_size}px"
            style.padding = "0 10px"
            style.margin = "0"

            document.body.appendChild(element)
            self.element = element
            self.move(rect)
        except Exception:
            # A browser that will not have it is not worth crashing over;
            # the canvas field still works with a hardware keyboard.
            self.element = None

    # -- geometry ---------------------------------------------------------

    def move(self, rect) -> None:
        """Place the element over `rect`, which is in device pixels.

        The page lays out in CSS pixels, so the rect is divided back down by
        the display scale -- the one place the two coordinate systems have
        to meet.
        """
        if self.element is None or rect == self._rect:
            return
        self._rect = rect
        try:
            style = self.element.style
            style.left = f"{rect.x / SCALE:.1f}px"
            style.top = f"{rect.y / SCALE:.1f}px"
            style.width = f"{rect.width / SCALE:.1f}px"
            style.height = f"{rect.height / SCALE:.1f}px"
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
        document = browser_document()
        if self.element is None or document is None:
            return False
        try:
            return document.activeElement is self.element
        except Exception:
            return False

    def destroy(self) -> None:
        """Remove the element. Leaking these leaves invisible inputs on the
        page that keep catching taps meant for the game."""
        if self.element is None:
            return
        try:
            self.element.remove()
        except Exception:
            pass
        self.element = None
