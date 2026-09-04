"""Named colours that carry their pixels with them.

Hair and eye colour are read by prose ("ash blonde") and by the paperdoll
(an RGB triple). Keeping both on one object means the two can never disagree
-- the alternative is a colour name table in the model and a second colour
table in the renderer, drifting apart.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Colour:
    name: str
    rgb: tuple[int, int, int]

    #: Groups colours for prose that wants the family, not the shade.
    family: str = ""

    def __str__(self) -> str:
        return self.name


HAIR_COLOURS = (
    Colour("black", (28, 26, 30), "dark"),
    Colour("raven", (40, 38, 52), "dark"),
    Colour("dark brown", (58, 42, 32), "brown"),
    Colour("chestnut", (96, 60, 38), "brown"),
    Colour("auburn", (124, 58, 34), "red"),
    Colour("copper", (168, 84, 38), "red"),
    Colour("ginger", (196, 112, 52), "red"),
    Colour("ash blonde", (188, 172, 140), "blonde"),
    Colour("golden blonde", (216, 182, 104), "blonde"),
    Colour("platinum", (226, 220, 206), "pale"),
    Colour("white", (238, 236, 234), "pale"),
    Colour("silver", (176, 178, 186), "pale"),
)

EYE_COLOURS = (
    Colour("dark brown", (58, 40, 28), "brown"),
    Colour("hazel", (122, 96, 46), "brown"),
    Colour("amber", (176, 124, 42), "warm"),
    Colour("green", (78, 118, 74), "cool"),
    Colour("grey", (132, 136, 142), "cool"),
    Colour("blue", (86, 122, 160), "cool"),
    Colour("pale blue", (150, 182, 206), "cool"),
    Colour("violet", (122, 96, 158), "uncanny"),
    Colour("red", (156, 62, 58), "uncanny"),
    Colour("gold", (206, 172, 76), "uncanny"),
)

_BY_NAME = {c.name: c for c in HAIR_COLOURS + EYE_COLOURS}


def colour(name: str) -> Colour:
    try:
        return _BY_NAME[name]
    except KeyError:
        raise KeyError(f"Unknown colour {name!r}") from None
