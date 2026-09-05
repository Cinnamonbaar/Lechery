"""Driving the dynamic-avatar-drawer from the game's traits.

The library is a browser thing: it draws a stack of canvases into a DOM
element. So the drawn avatar exists only in the web build, and the
placeholder figure stays for the desktop. That is a real cost and worth
naming -- appearance is now something the desktop build cannot show.

This module owns the mapping from our traits to the library's dimensions,
which is the only interesting part. Its dimensions are in its own units and
its own ranges; ours are in centimetres and cup sizes. Everything that
translates between the two lives here so that neither model has to know
about the other.
"""

from __future__ import annotations

import colorsys
from typing import Optional

from ..traits import Character
from ..traits.scale import BUST, HEIGHT, PHALLUS
from . import dom

#: The library's own canvas size. Ours is scaled to fit whatever box the
#: paperdoll panel gives it.
NATIVE_SIZE = (700, 1200)

#: `fem` is the library's core stat: "how overall feminine their appearance
#: is; influences a lot of dimensions". Range 0-11, average 5.
FEM_LOW, FEM_HIGH = 0.0, 11.0


def available() -> bool:
    """Whether the drawn avatar can be used at all."""
    return dom.in_browser()


def ready() -> bool:
    """Whether the library has finished loading and drawn something."""
    return dom.evaluate(
        "window.LecheryAvatar ? String(window.LecheryAvatar.ready()) : 'false'"
    ) == "true"


def status() -> str:
    """One word for what the library is doing, or why it is not.

    There is no console on a phone, so a failure in the page is otherwise
    completely silent -- the panel draws this instead of an empty box.
    """
    reported = dom.evaluate(
        # Reports what is actually in the page, so a missing script and a
        # library that failed to load are not the same word.
        "window.LecheryAvatar ? window.LecheryAvatar.status()"
        " : ('no bridge (da=' + (typeof da) + ')')"
    )
    if reported is None:
        return "no browser"
    return reported


# -- the mapping ----------------------------------------------------------


def _scaled(value: float, scale, low: float, high: float) -> float:
    """Put a trait on one of the library's ranges, proportionally."""
    span = scale.maximum - scale.minimum
    if span <= 0:
        return low
    fraction = (float(value) - scale.minimum) / span
    return low + max(0.0, min(1.0, fraction)) * (high - low)


def femininity(character: Character) -> float:
    """The library's `fem` stat, from how the character reads.

    A happy coincidence: their core stat and our perception model are the
    same idea. Ours runs -1 to +1 and already accounts for build, so it
    maps straight onto their 0-11 without inventing anything.

    Read undressed, because this is the body the drawing shows.
    """
    from ..traits.perception import NUDE

    score = character.presentation(NUDE).score  # -1 .. +1
    return FEM_LOW + (score + 1.0) / 2.0 * (FEM_HIGH - FEM_LOW)


def hair_hsl(character: Character) -> tuple[float, float, float]:
    """Hair colour as the library wants it: hue, saturation, lightness.

    Our palette carries RGB, since that is what the placeholder figure
    draws with. Converting here keeps one source of truth for what
    "copper" means rather than a second colour table in another format.
    """
    colour = character.traits.get("hair_colour")
    rgb = getattr(colour, "rgb", (90, 70, 60))
    hue, lightness, saturation = colorsys.rgb_to_hls(*[c / 255 for c in rgb])
    return (hue * 360.0, saturation * 100.0, lightness * 100.0)


def dimensions(character: Character) -> dict[str, float]:
    """Every library dimension we currently have an opinion about.

    Deliberately partial. The library has thirty-odd dimensions and we have
    six traits; anything not named here keeps the library's own default,
    which is a sensible average rather than a zero.
    """
    traits = character.traits
    hue, saturation, lightness = hair_hsl(character)

    return {
        # Their height is in centimetres too, so this one is a straight copy.
        "height": float(traits.get("height", 170)),
        # Cup index onto their 0-100ish scale.
        "breastSize": _scaled(traits.get("bust", 0), BUST, 0.0, 100.0),
        "penisSize": _scaled(traits.get("phallus", 0), PHALLUS, 0.0, 100.0),
        "hairHue": hue,
        "hairSaturation": saturation,
        "hairLightness": lightness,
    }


def payload(character: Character) -> dict:
    """What the shim needs to build a player."""
    return {
        "name": character.name,
        "fem": femininity(character),
        "basedim": dimensions(character),
    }


def signature(character: Character) -> tuple:
    """What the drawing depends on, for deciding when to redraw.

    Compared rather than subscribed to, for the same reason the placeholder
    figure does it: a trait changed by a path that forgot to notify cannot
    leave a stale drawing.
    """
    data = payload(character)
    return (data["name"], round(data["fem"], 3)) + tuple(
        round(value, 3) for _, value in sorted(data["basedim"].items())
    )


# -- driving the page -----------------------------------------------------


class Avatar:
    """The drawn figure, positioned over a rect the panel chooses.

    It lives in the page, not on the game's canvas, so it does not
    disappear just because the thing that placed it stopped drawing. The
    frame protocol handles that: whoever wants it visible must say so every
    frame, and `frame_done` takes it away when nobody did.
    """

    def __init__(self) -> None:
        self._signature: Optional[tuple] = None
        self._rect = None
        self.visible = False
        self._placed_this_frame = False

    def update(self, character: Character) -> bool:
        """Redraw if the character changed. Returns whether it did."""
        current = signature(character)
        if current == self._signature:
            return False
        self._signature = current
        dom.call_json("LecheryAvatar.update", payload(character))
        return True

    def place(self, rect) -> None:
        """Show the avatar over `rect`, given in device pixels."""
        self._rect = rect
        self._placed_this_frame = True
        if rect == self._rect and self.visible:
            return
        left, top, width, height = dom.css_geometry(rect)
        dom.call("LecheryAvatar.place", left, top, width, height)
        self.visible = True

    def hide(self) -> None:
        if not self.visible:
            return
        dom.call("LecheryAvatar.hide")
        self.visible = False

    def frame_done(self) -> None:
        """End of frame: hide unless something asked for it.

        Without this the figure stays over whatever replaced the screen
        that was showing it -- the menu, most obviously, which does not
        draw the paperdoll panel at all.
        """
        if not self._placed_this_frame:
            self.hide()
        self._placed_this_frame = False


#: One avatar, because there is one element in the page.
_SHARED = Avatar()


def shared() -> Avatar:
    return _SHARED


def frame_done() -> None:
    _SHARED.frame_done()
