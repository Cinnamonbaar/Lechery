"""The application: a stack of screens, and the frame that drives them.

The app owns everything a screen should not have to re-derive -- the window
size, the settings, the form factor -- and nothing else. Game state belongs
to the session, and the session belongs to the play screen, so returning to
the menu and starting again cannot leave a stale world behind.
"""

from __future__ import annotations

from typing import Optional

import pygame

from ..session import Session
from ..settings import LayoutMode, Settings
from .profile import FormFactor, resolve
from .screens.base import Screen

BACKGROUND = (12, 11, 14)


class App:
    def __init__(
        self,
        size: tuple[int, int],
        settings: Optional[Settings] = None,
        screen: Optional[Screen] = None,
    ) -> None:
        self.window = size
        self.settings = settings or Settings()
        self.form = resolve(self.settings.layout_mode, size)
        self.running = True
        self.screens: list[Screen] = []

        if screen is None:
            from .screens.menu import MainMenu

            screen = MainMenu()
        self.push(screen)

    # -- the stack --------------------------------------------------------

    @property
    def screen(self) -> Screen:
        return self.screens[-1]

    def push(self, screen: Screen) -> Screen:
        self.screens.append(screen)
        screen.enter(self)
        return screen

    def pop(self) -> Optional[Screen]:
        """Leave the top screen. Quitting the last one quits the game."""
        if len(self.screens) <= 1:
            self.quit()
            return None
        screen = self.screens.pop()
        screen.leave()
        self.screen.resize(self.window)
        return screen

    def replace(self, screen: Screen) -> Screen:
        """Swap the top screen out. Used where there is no going back."""
        if self.screens:
            self.screens.pop().leave()
        return self.push(screen)

    def quit(self) -> None:
        self.running = False

    # -- shared state -----------------------------------------------------

    def set_layout_mode(self, mode: LayoutMode) -> None:
        self.settings.layout_mode = mode
        self._refresh_form()
        self.settings.save()

    def _refresh_form(self) -> None:
        form = resolve(self.settings.layout_mode, self.window)
        changed = form is not self.form
        self.form = form
        for screen in self.screens:
            screen.resize(self.window)
        return changed

    def start_game(self, character, *, opening: str = "", seed: Optional[int] = None) -> None:
        """Leave creation behind and begin play.

        `replace` rather than `push`: there is no going back into character
        creation once the world exists, and leaving it on the stack would
        mean an Escape from the game landed in a half-built creator.
        """
        from .screens.play import PlayScreen

        session = Session.new_game(seed, character=character)
        if opening:
            session.log.prose(opening)
        self.replace(PlayScreen(session, self.window, self.settings))

    # -- the frame --------------------------------------------------------

    def resize(self, size: tuple[int, int]) -> None:
        """Adopt a new window size, re-picking the layout if it changed shape.

        Called for a desktop resize and for a browser rotating; both are the
        same event as far as anything downstream is concerned.
        """
        self.window = size
        self._refresh_form()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.VIDEORESIZE:
            self.resize((event.w, event.h))
            return
        self.screen.handle_event(event)

    def update(self, dt: float) -> None:
        self.screen.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(BACKGROUND)
        # Draw down to the last opaque screen, then back up, so a
        # transparent overlay shows what it is covering.
        first = len(self.screens) - 1
        while first > 0 and self.screens[first].transparent:
            first -= 1
        for screen in self.screens[first:]:
            screen.draw(surface)

    def step(self, surface: pygame.Surface, events, dt: float) -> bool:
        """One whole frame. Returns whether to keep going.

        The loop that calls this is async under pygbag and plain on the
        desktop, so the frame itself contains neither -- both loops share
        every line that matters, and a test can drive this synchronously.
        """
        for event in events:
            if event.type == pygame.QUIT:
                return False
            self.handle_event(event)

        if not self.running:
            return False

        self.update(dt)
        self.draw(surface)
        return True
