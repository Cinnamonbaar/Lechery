"""The paperdoll bar: the character as they actually look.

There is no appearance model yet, so this is the *structure* rather than a
preview: an ordered stack of named slots, composited bottom-up, each drawing
a placeholder shape. When traits exist, a slot's placeholder is swapped for a
sprite and nothing else here changes.

The composite is cached and rebuilt only when the character changes, not
every frame. That is the choice worth making early: layered paperdolls are
cheap to draw and expensive to assemble, and a game where appearance shifts
constantly will assemble them far more often than a normal one -- but still
far less often than sixty times a second.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

import pygame

from ..traits import Character
from ..traits.scale import BUST, HEIGHT

BACKDROP = (26, 23, 30)
FIGURE = (96, 96, 106)
FIGURE_EDGE = (58, 58, 66)
HAIR = (74, 70, 80)
LABEL = (110, 104, 116)

#: Slots in draw order, back to front. The order is the whole contract: a
#: sprite added to a slot lands at the right depth without touching code.
SLOTS = (
    "backdrop",
    "tail",
    "body",
    "legs",
    "torso",
    "arms",
    "head",
    "hair",
    "eyes",
    "worn",
    "held",
)


@dataclass
class Slot:
    """One layer of the composite."""

    name: str
    draw: Callable[[pygame.Surface, pygame.Rect], None]
    visible: bool = True


class Paperdoll:
    """Composites the character portrait from its slots."""

    def __init__(self, size: tuple[int, int], character: Optional[Character] = None) -> None:
        self.size = size
        self.character = character
        self.slots: dict[str, Slot] = {}
        self._cache: Optional[pygame.Surface] = None
        self._dirty = True
        self._signature: Optional[tuple] = None
        self._install_placeholders()

    # -- reacting to the character ----------------------------------------

    def signature(self) -> tuple:
        """The traits this drawing depends on.

        Compared per frame to decide whether to recomposite. Cheaper than
        subscribing to every trait, and it cannot go stale if a trait is
        changed by a path that forgot to notify.
        """
        if self.character is None:
            return ()
        traits = self.character.traits
        return (
            traits.get("height"),
            traits.get("bust"),
            getattr(traits.get("hair_colour"), "rgb", None),
            getattr(traits.get("eye_colour"), "rgb", None),
            self.size,
        )

    def refresh(self) -> None:
        signature = self.signature()
        if signature != self._signature:
            self._signature = signature
            self._dirty = True

    # -- slots ------------------------------------------------------------

    def set_slot(self, name: str, draw: Callable[[pygame.Surface, pygame.Rect], None]) -> None:
        if name not in SLOTS:
            raise KeyError(f"Unknown paperdoll slot {name!r}; add it to SLOTS")
        self.slots[name] = Slot(name=name, draw=draw)
        self._dirty = True

    def clear_slot(self, name: str) -> None:
        self.slots.pop(name, None)
        self._dirty = True

    def resize(self, size: tuple[int, int]) -> None:
        if size != self.size:
            self.size = size
            self._dirty = True

    # -- rendering --------------------------------------------------------

    def surface(self) -> pygame.Surface:
        self.refresh()
        if self._cache is None or self._dirty:
            self._cache = self._composite()
            self._dirty = False
        return self._cache

    def _composite(self) -> pygame.Surface:
        width, height = self.size
        surface = pygame.Surface((max(width, 1), max(height, 1)), pygame.SRCALPHA)
        rect = surface.get_rect()
        for name in SLOTS:
            slot = self.slots.get(name)
            if slot is not None and slot.visible:
                slot.draw(surface, rect)
        return surface

    # -- placeholder art --------------------------------------------------

    def _trait(self, key: str, default: float) -> float:
        if self.character is None:
            return default
        return float(self.character.traits.get(key, default))

    def _colour(self, key: str, default: tuple[int, int, int]) -> tuple[int, int, int]:
        if self.character is None:
            return default
        value = self.character.traits.get(key)
        return getattr(value, "rgb", default)

    def _stature(self) -> float:
        """How much of the panel the figure fills, from its height trait.

        Scaled to a narrow range: a towering character should read as taller
        than a short one, but not so much that the short one becomes a
        thumbnail in the same box.
        """
        height = self._trait("height", 170)
        span = HEIGHT.maximum - HEIGHT.minimum
        return 0.82 + 0.18 * ((height - HEIGHT.minimum) / span)

    def _install_placeholders(self) -> None:
        """A featureless figure drawn from primitives.

        Schematic on purpose: it reflects colouring, stature and build so
        changes are visible, and stops there. It is scaffolding for real art,
        not an attempt at it.
        """

        def backdrop(surface: pygame.Surface, rect: pygame.Rect) -> None:
            pygame.draw.rect(surface, BACKDROP, rect, border_radius=4)

        def figure_rect(rect: pygame.Rect) -> pygame.Rect:
            """The box the body occupies, shrunk from the panel by stature."""
            height = rect.height * self._stature()
            box = pygame.Rect(0, 0, rect.width, height)
            box.midbottom = rect.midbottom
            return box

        def legs(surface: pygame.Surface, rect: pygame.Rect) -> None:
            box = figure_rect(rect)
            top = box.y + box.height * 0.56
            bottom = box.y + box.height * 0.94
            for side in (-1, 1):
                leg = pygame.Rect(0, 0, box.width * 0.13, bottom - top)
                leg.midtop = (box.centerx + side * box.width * 0.09, top)
                pygame.draw.rect(surface, FIGURE, leg, border_radius=int(box.width * 0.06))
                pygame.draw.rect(surface, FIGURE_EDGE, leg, width=1, border_radius=int(box.width * 0.06))

        def torso(surface: pygame.Surface, rect: pygame.Rect) -> None:
            box = figure_rect(rect)
            body = pygame.Rect(0, 0, box.width * 0.34, box.height * 0.34)
            body.midtop = (box.centerx, box.y + box.height * 0.26)
            pygame.draw.rect(surface, FIGURE, body, border_radius=int(box.width * 0.1))
            pygame.draw.rect(surface, FIGURE_EDGE, body, width=1, border_radius=int(box.width * 0.1))

            # Build reads as a widening of the chest, one step per band --
            # enough to see a change, and no more than a schematic should say.
            band = BUST.index(self._trait("bust", 0))
            if band:
                width = box.width * (0.30 + 0.035 * band)
                chest = pygame.Rect(0, 0, width, box.height * 0.10)
                chest.center = (box.centerx, body.y + body.height * 0.24)
                pygame.draw.ellipse(surface, FIGURE, chest)
                pygame.draw.ellipse(surface, FIGURE_EDGE, chest, width=1)

        def arms(surface: pygame.Surface, rect: pygame.Rect) -> None:
            box = figure_rect(rect)
            top = box.y + box.height * 0.28
            for side in (-1, 1):
                arm = pygame.Rect(0, 0, box.width * 0.1, box.height * 0.3)
                arm.midtop = (box.centerx + side * box.width * 0.22, top)
                pygame.draw.rect(surface, FIGURE, arm, border_radius=int(box.width * 0.05))
                pygame.draw.rect(surface, FIGURE_EDGE, arm, width=1, border_radius=int(box.width * 0.05))

        def head(surface: pygame.Surface, rect: pygame.Rect) -> None:
            box = figure_rect(rect)
            radius = box.width * 0.11
            centre = (box.centerx, box.y + box.height * 0.17)
            pygame.draw.circle(surface, FIGURE, centre, radius)
            pygame.draw.circle(surface, FIGURE_EDGE, centre, radius, width=1)

        def eyes(surface: pygame.Surface, rect: pygame.Rect) -> None:
            box = figure_rect(rect)
            colour = self._colour("eye_colour", (120, 110, 100))
            radius = max(1.5, box.width * 0.018)
            y = box.y + box.height * 0.168
            for side in (-1, 1):
                pygame.draw.circle(surface, colour, (box.centerx + side * box.width * 0.045, y), radius)

        def hair(surface: pygame.Surface, rect: pygame.Rect) -> None:
            box = figure_rect(rect)
            colour = self._colour("hair_colour", HAIR)
            radius = box.width * 0.12
            cap = pygame.Rect(0, 0, radius * 2, radius * 1.35)
            cap.midtop = (box.centerx, box.y + box.height * 0.17 - radius)
            pygame.draw.ellipse(surface, colour, cap)

        self.set_slot("backdrop", backdrop)
        self.set_slot("legs", legs)
        self.set_slot("torso", torso)
        self.set_slot("arms", arms)
        self.set_slot("head", head)
        self.set_slot("hair", hair)
        self.set_slot("eyes", eyes)
