"""Screens, and the stack they live on.

A stack rather than a single current screen, so a screen can be laid over
one that is still there -- a settings panel over the menu, a dialogue over
the world. The screen underneath keeps its state and is redrawn when the
one above pops, which is what makes "back" cheap.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import pygame

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ..app import App


class Screen:
    """One layer of the interface."""

    #: When True the screen below is drawn first, and this one over it.
    transparent = False

    def __init__(self) -> None:
        self.app: Optional["App"] = None

    # -- lifecycle --------------------------------------------------------

    def enter(self, app: "App") -> None:
        """Called when pushed. The app is not available before this."""
        self.app = app

    def leave(self) -> None:
        """Called when popped or replaced."""

    def resize(self, window: tuple[int, int]) -> None:
        """Called when the window or form factor changes."""

    # -- frame ------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Returns whether the event was consumed."""
        return False

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        pass
