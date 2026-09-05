"""The main menu.

The first thing anyone sees, so it states what the game is and gets out of
the way. Continue is present but disabled until saving exists, rather than
hidden: a menu that grows items later teaches players to re-read it every
time, and a greyed row tells them the feature is coming.
"""

from __future__ import annotations

import pygame

from ...settings import LayoutMode
from ..fonts import load as load_font
from ..text import TextStyle
from ..widgets import ACCENT, MUTED, Button, Paragraph
from .base import Screen

BACKGROUND = (13, 12, 16)
TITLE = (226, 200, 148)
RULE = (52, 46, 60)

BUTTON_WIDTH = 300
BUTTON_HEIGHT = 46
BUTTON_GAP = 12


class MainMenu(Screen):
    def __init__(self) -> None:
        super().__init__()
        self.title_font = load_font("heading", 54, bold=True)
        self.body = TextStyle(load_font("body", 16))
        self.small = TextStyle(load_font("body", 14))
        self.buttons: list[Button] = []
        self.tagline = Paragraph(
            self.small,
            "A transformation RPG. You were somewhere else this morning.",
            MUTED,
        )

    def enter(self, app) -> None:
        super().enter(app)
        self._build()

    def resize(self, window: tuple[int, int]) -> None:
        self._build()

    def _build(self) -> None:
        if self.app is None:
            return
        width, height = self.app.window
        x = width // 2 - BUTTON_WIDTH // 2
        y = int(height * 0.44)

        def row() -> pygame.Rect:
            nonlocal y
            rect = pygame.Rect(x, y, BUTTON_WIDTH, BUTTON_HEIGHT)
            y += BUTTON_HEIGHT + BUTTON_GAP
            return rect

        new_game = Button(row(), "New Game", self.body, self._new_game, primary=True)

        # Present but disabled: hiding it would mean the menu changes shape
        # the first time a save exists, which teaches players to re-read it.
        cont = Button(row(), "Continue", self.body, None)
        cont.enabled = False

        layout = Button(row(), self._layout_label(), self.body, self._cycle_layout)
        self._layout_button = layout

        self.buttons = [new_game, cont, layout, Button(row(), "Quit", self.body, self._quit)]

    # -- actions ----------------------------------------------------------

    def _new_game(self) -> None:
        from .creation import CharacterCreation

        self.app.push(CharacterCreation())

    def _layout_label(self) -> str:
        return f"Layout: {self.app.settings.layout_mode.value}"

    def _cycle_layout(self) -> None:
        order = list(LayoutMode)
        current = order.index(self.app.settings.layout_mode)
        self.app.set_layout_mode(order[(current + 1) % len(order)])
        self._layout_button.label = self._layout_label()

    def _quit(self) -> None:
        self.app.quit()

    # -- frame ------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> bool:
        for button in self.buttons:
            if button.handle_event(event):
                return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(BACKGROUND)
        width, height = surface.get_size()

        title = self.title_font.render("Lechery", True, TITLE)
        surface.blit(title, title.get_rect(midtop=(width // 2, int(height * 0.20))))

        rule_y = int(height * 0.20) + title.get_height() + 14
        pygame.draw.line(
            surface, RULE, (width // 2 - 120, rule_y), (width // 2 + 120, rule_y)
        )

        self.tagline.draw(
            surface, pygame.Rect(width // 2 - 200, rule_y + 16, 400, 40)
        )

        for button in self.buttons:
            button.draw(surface)
