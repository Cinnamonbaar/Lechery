"""The left bar: the paperdoll, and the character's name under it."""

from __future__ import annotations

import pygame

from ..entities.actor import Player
from .paperdoll import LABEL, Paperdoll
from .panel import Panel
from .text import TextStyle

#: Figure aspect ratio (width:height). Portraits are taller than wide.
ASPECT = 0.62


class PaperdollPanel(Panel):
    def __init__(self, player: Player, style: TextStyle, tab_style: TextStyle) -> None:
        super().__init__("Self", style, tab_style)
        self.player = player
        self.doll = Paperdoll((1, 1))
        self.style = style

    def draw_body(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        height = min(rect.height - 30, int(rect.width / ASPECT))
        width = int(height * ASPECT)
        if width <= 0 or height <= 0:
            return

        self.doll.resize((width, height))
        figure = self.doll.surface()
        surface.blit(figure, figure.get_rect(midtop=(rect.centerx, rect.y)))

        note = self.style.font.render("appearance pending", True, LABEL)
        surface.blit(note, note.get_rect(midtop=(rect.centerx, rect.y + height + 10)))
