"""The root view: three panes, and the events that reach them.

Owns the layout and hands each pane its rect every frame, so a collapse or a
window resize needs no cached geometry anywhere else.
"""

from __future__ import annotations

import pygame

from ..session import Session
from .layout import ScreenLayout
from .logpanel import LogPanel
from .paperdollpanel import PaperdollPanel
from .text import TextStyle
from .worldview import WorldView

BACKGROUND = (12, 11, 14)


class App:
    def __init__(self, session: Session, size: tuple[int, int]) -> None:
        self.session = session
        self.layout = ScreenLayout(window=size)

        body = TextStyle(pygame.font.SysFont("georgia,serif", 15))
        heading = TextStyle(pygame.font.SysFont("georgia,serif", 13, bold=True))
        tab = TextStyle(pygame.font.SysFont("georgia,serif", 12, bold=True))

        self.paperdoll = PaperdollPanel(session.player, body, tab)
        self.log = LogPanel(session.log, body, tab)
        self.paperdoll.style = heading
        self.world = WorldView(session, self.layout.center)

    # -- input ------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.VIDEORESIZE:
            self.layout.window = (event.w, event.h)
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFTBRACKET:
                self.layout.toggle_left()
                return
            if event.key == pygame.K_RIGHTBRACKET:
                self.layout.toggle_right()
                return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # A collapsed bar is a click target; that thin tab is the only
            # way back, so it must be the easiest thing on screen to hit.
            if not self.layout.left_open and self.layout.left.collidepoint(event.pos):
                self.layout.toggle_left()
                return
            if not self.layout.right_open and self.layout.right.collidepoint(event.pos):
                self.layout.toggle_right()
                return

        self.log.handle_event(event)
        self.paperdoll.handle_event(event)

    def update(self, dt: float) -> None:
        # The world view is told its rect before it reads input, so aiming
        # is measured against the pane the player is actually looking at.
        self.world.rect = self.layout.center
        self.world.update(dt)

    # -- drawing ----------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(BACKGROUND)

        self.world.rect = self.layout.center
        self.world.draw(surface)

        self.paperdoll.open = self.layout.left_open
        self.log.open = self.layout.right_open
        self.paperdoll.draw(surface, self.layout.left)
        self.log.draw(surface, self.layout.right)
