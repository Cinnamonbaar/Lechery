"""Shared chrome for the side bars."""

from __future__ import annotations

import pygame

from .text import TextStyle

PANEL_BG = (21, 19, 25)
PANEL_EDGE = (44, 40, 52)
TAB_BG = (28, 25, 33)
TAB_HOVER = (46, 42, 56)
TITLE = (196, 172, 128)
TAB_LABEL = (128, 120, 132)

TITLE_HEIGHT = 34
PAD = 14


class Panel:
    """A side bar that can be drawn open or collapsed to a tab."""

    def __init__(self, title: str, style: TextStyle, tab_style: TextStyle) -> None:
        self.title = title
        self.style = style
        self.tab_style = tab_style
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.open = True
        self.hovered = False

    # -- frame ------------------------------------------------------------

    def draw(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        self.rect = rect
        if self.open:
            self._draw_open(surface, rect)
        else:
            self._draw_tab(surface, rect)

    def _draw_open(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        pygame.draw.rect(surface, PANEL_BG, rect)
        pygame.draw.rect(surface, PANEL_EDGE, rect, width=1)

        label = self.style.font.render(self.title.upper(), True, TITLE)
        surface.blit(label, (rect.x + PAD, rect.y + 10))
        line_y = rect.y + TITLE_HEIGHT
        pygame.draw.line(
            surface, PANEL_EDGE, (rect.x + PAD, line_y), (rect.right - PAD, line_y)
        )

        body = rect.copy()
        body.y = line_y + PAD
        body.height = rect.height - (line_y - rect.y) - PAD * 2
        body.x += PAD
        body.width -= PAD * 2
        if body.width > 0 and body.height > 0:
            self.draw_body(surface, body)

    def _draw_tab(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """Collapsed: a thin strip carrying the panel's name sideways."""
        pygame.draw.rect(surface, TAB_HOVER if self.hovered else TAB_BG, rect)
        pygame.draw.rect(surface, PANEL_EDGE, rect, width=1)

        label = self.tab_style.font.render(self.title.upper(), True, TAB_LABEL)
        rotated = pygame.transform.rotate(label, 90)
        surface.blit(rotated, rotated.get_rect(center=rect.center))

    # -- subclasses -------------------------------------------------------

    def draw_body(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """Draw the panel's contents into `rect`. Overridden."""

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Returns whether the event was consumed."""
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        return False
