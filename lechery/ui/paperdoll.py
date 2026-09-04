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

    def __init__(self, size: tuple[int, int]) -> None:
        self.size = size
        self.slots: dict[str, Slot] = {}
        self._cache: Optional[pygame.Surface] = None
        self._dirty = True
        self._install_placeholders()

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

    # -- placeholders -----------------------------------------------------

    def _install_placeholders(self) -> None:
        """A featureless standing figure, drawn from primitives.

        Front-facing and neutral on purpose: this is scaffolding to hang
        real art on, not a guess at what the character looks like.
        """

        def backdrop(surface: pygame.Surface, rect: pygame.Rect) -> None:
            pygame.draw.rect(surface, BACKDROP, rect, border_radius=4)

        def legs(surface: pygame.Surface, rect: pygame.Rect) -> None:
            width = rect.width
            top = rect.y + rect.height * 0.56
            bottom = rect.y + rect.height * 0.94
            for side in (-1, 1):
                x = rect.centerx + side * width * 0.09
                leg = pygame.Rect(0, 0, width * 0.13, bottom - top)
                leg.midtop = (x, top)
                pygame.draw.rect(surface, FIGURE, leg, border_radius=int(width * 0.06))
                pygame.draw.rect(surface, FIGURE_EDGE, leg, width=1, border_radius=int(width * 0.06))

        def torso(surface: pygame.Surface, rect: pygame.Rect) -> None:
            body = pygame.Rect(0, 0, rect.width * 0.34, rect.height * 0.34)
            body.midtop = (rect.centerx, rect.y + rect.height * 0.26)
            pygame.draw.rect(surface, FIGURE, body, border_radius=int(rect.width * 0.1))
            pygame.draw.rect(surface, FIGURE_EDGE, body, width=1, border_radius=int(rect.width * 0.1))

        def arms(surface: pygame.Surface, rect: pygame.Rect) -> None:
            top = rect.y + rect.height * 0.28
            height = rect.height * 0.3
            for side in (-1, 1):
                arm = pygame.Rect(0, 0, rect.width * 0.1, height)
                arm.midtop = (rect.centerx + side * rect.width * 0.22, top)
                pygame.draw.rect(surface, FIGURE, arm, border_radius=int(rect.width * 0.05))
                pygame.draw.rect(surface, FIGURE_EDGE, arm, width=1, border_radius=int(rect.width * 0.05))

        def head(surface: pygame.Surface, rect: pygame.Rect) -> None:
            radius = rect.width * 0.11
            centre = (rect.centerx, rect.y + rect.height * 0.17)
            pygame.draw.circle(surface, FIGURE, centre, radius)
            pygame.draw.circle(surface, FIGURE_EDGE, centre, radius, width=1)

        def hair(surface: pygame.Surface, rect: pygame.Rect) -> None:
            radius = rect.width * 0.12
            cap = pygame.Rect(0, 0, radius * 2, radius * 1.3)
            cap.midtop = (rect.centerx, rect.y + rect.height * 0.17 - radius)
            pygame.draw.ellipse(surface, HAIR, cap)

        self.set_slot("backdrop", backdrop)
        self.set_slot("legs", legs)
        self.set_slot("torso", torso)
        self.set_slot("arms", arms)
        self.set_slot("head", head)
        self.set_slot("hair", hair)
