"""The left bar: the paperdoll, and the character's traits under it."""

from __future__ import annotations

import pygame

from ..entities.actor import Player
from ..traits import TRAITS
from .paperdoll import LABEL, Paperdoll
from .panel import Panel
from .text import TextStyle

#: Figure aspect ratio (width:height). Portraits are taller than wide.
ASPECT = 0.62

NAME = (222, 214, 206)
KEY = (122, 116, 128)
VALUE = (186, 180, 176)
ROW_GAP = 4

#: Traits shown under the figure, in this order. Not every trait: the bar is
#: a glance, not a character sheet, and the sheet can come later.
SHOWN = ("age", "height", "hair_colour", "eye_colour", "bust", "phallus")


class PaperdollPanel(Panel):
    def __init__(self, player: Player, style: TextStyle, tab_style: TextStyle) -> None:
        super().__init__("Self", style, tab_style)
        self.player = player
        self.doll = Paperdoll((1, 1), player.character)
        self.style = style
        self.body_style = style

    @property
    def character(self):
        return self.player.character

    def draw_body(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        rows = len(SHOWN) + 2
        text_height = rows * (self.body_style.line_height + ROW_GAP)

        height = min(rect.height - text_height, int(rect.width / ASPECT))
        width = int(height * ASPECT)
        if width <= 0 or height <= 0:
            return

        self.doll.resize((width, height))
        figure = self.doll.surface()
        surface.blit(figure, figure.get_rect(midtop=(rect.centerx, rect.y)))

        self._draw_traits(surface, rect, rect.y + height + 12)

    def _draw_traits(self, surface: pygame.Surface, rect: pygame.Rect, y: int) -> None:
        font = self.body_style.font
        character = self.character

        name = font.render(character.name, True, NAME)
        surface.blit(name, (rect.x, y))
        y += self.body_style.line_height + ROW_GAP

        gender = font.render(f"{character.gender}  ·  {character.pronouns}", True, KEY)
        surface.blit(gender, (rect.x, y))
        y += self.body_style.line_height + ROW_GAP + 4

        for key in SHOWN:
            if key not in character.traits:
                continue
            label = font.render(TRAITS[key].label, True, KEY)
            # Values are drawn right-aligned so the column reads as a table
            # and a changing number does not shuffle the label about.
            value = font.render(character.traits.describe(key), True, VALUE)
            surface.blit(label, (rect.x, y))
            surface.blit(value, (rect.right - value.get_width(), y))
            y += self.body_style.line_height + ROW_GAP
