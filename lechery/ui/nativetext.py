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
