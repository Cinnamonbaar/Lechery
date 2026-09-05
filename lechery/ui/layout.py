"""Screen layouts: where the three panes go.

Two arrangements behind one interface, so nothing downstream knows which it
is in. Both answer the same questions -- where is each pane, where is its
handle, and does the world need to draw underneath it.

WideLayout tiles the window: the bars take their width and the world gets
what is left. CompactLayout gives the whole window to the world and slides
one bar over it as a drawer, because on a phone-shaped screen a bar that
takes width leaves the world a letterbox.
"""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from .metrics import px
from .profile import FormFactor

#: Width of a bar when open, on a wide screen.
BAR_WIDTH = 268

#: Width of the tab left behind when a bar is collapsed.
TAB_WIDTH = 22

#: The centre pane never shrinks below this; bars give way first.
MIN_CENTER = 420

#: Compact drawers take most of the screen but never all of it -- leaving
#: the world visible behind an edge is what makes the drawer read as
#: temporary rather than as a screen change.
COMPACT_DRAWER_FRACTION = 0.82

#: Touch target size for the compact handles. Fingers are not cursors.
HANDLE_SIZE = 46
HANDLE_MARGIN = 10


@dataclass
class Layout:
    """Base: window size and which bars are open."""

    window: tuple[int, int]
    left_open: bool = True
    right_open: bool = True

    #: Whether bars are drawn over the world rather than beside it.
    overlays = False

    form = FormFactor.WIDE

    def toggle_left(self) -> None:
        self.left_open = not self.left_open

    def toggle_right(self) -> None:
        self.right_open = not self.right_open

    # Subclasses provide: left, right, center, left_handle, right_handle.


class WideLayout(Layout):
    """Three panes side by side."""

    overlays = False
    form = FormFactor.WIDE

    def _bar_widths(self) -> tuple[int, int]:
        left = px(BAR_WIDTH) if self.left_open else px(TAB_WIDTH)
        right = px(BAR_WIDTH) if self.right_open else px(TAB_WIDTH)

        # A narrow window shrinks the bars rather than the play area; both
        # give way together so the centre stays centred.
        overflow = (left + right + px(MIN_CENTER)) - self.window[0]
        if overflow > 0:
            if self.left_open and self.right_open:
                left -= overflow // 2
                right -= overflow - overflow // 2
            elif self.left_open:
                left -= overflow
            elif self.right_open:
                right -= overflow
            left = max(left, px(TAB_WIDTH))
            right = max(right, px(TAB_WIDTH))
        return left, right

    @property
    def left(self) -> pygame.Rect:
        left, _ = self._bar_widths()
        return pygame.Rect(0, 0, left, self.window[1])

    @property
    def right(self) -> pygame.Rect:
        _, right = self._bar_widths()
        return pygame.Rect(self.window[0] - right, 0, right, self.window[1])

    @property
    def center(self) -> pygame.Rect:
        left, right = self._bar_widths()
        return pygame.Rect(left, 0, max(self.window[0] - left - right, 1), self.window[1])

    @property
    def left_handle(self) -> pygame.Rect:
        """The whole collapsed strip is the handle, and it is always there."""
        return self.left

    @property
    def right_handle(self) -> pygame.Rect:
        return self.right


class CompactLayout(Layout):
    """One pane at a time; bars slide over the world as drawers."""

    overlays = True
    form = FormFactor.COMPACT

    def __init__(self, window: tuple[int, int], left_open: bool = False, right_open: bool = False):
        # Both bars start closed: on a small screen the world is what the
        # player came for, and a drawer covering it on launch reads as a menu.
        super().__init__(window=window, left_open=left_open, right_open=right_open)

    def toggle_left(self) -> None:
        """Opening one drawer closes the other; they would overlap."""
        self.left_open = not self.left_open
        if self.left_open:
            self.right_open = False

    def toggle_right(self) -> None:
        self.right_open = not self.right_open
        if self.right_open:
            self.left_open = False

    def _drawer_width(self) -> int:
        return int(min(self.window[0] * COMPACT_DRAWER_FRACTION, px(BAR_WIDTH * 1.6)))

    @property
    def left(self) -> pygame.Rect:
        if not self.left_open:
            return pygame.Rect(0, 0, 0, self.window[1])
        return pygame.Rect(0, 0, self._drawer_width(), self.window[1])

    @property
    def right(self) -> pygame.Rect:
        if not self.right_open:
            return pygame.Rect(self.window[0], 0, 0, self.window[1])
        width = self._drawer_width()
        return pygame.Rect(self.window[0] - width, 0, width, self.window[1])

    @property
    def center(self) -> pygame.Rect:
        """The world always gets the whole window; drawers cover it."""
        return pygame.Rect(0, 0, max(self.window[0], 1), max(self.window[1], 1))

    @property
    def left_handle(self) -> pygame.Rect:
        return pygame.Rect(px(HANDLE_MARGIN), px(HANDLE_MARGIN), px(HANDLE_SIZE), px(HANDLE_SIZE))

    @property
    def right_handle(self) -> pygame.Rect:
        return pygame.Rect(
            self.window[0] - px(HANDLE_SIZE) - px(HANDLE_MARGIN),
            px(HANDLE_MARGIN),
            px(HANDLE_SIZE),
            px(HANDLE_SIZE),
        )


def make_layout(form: FormFactor, window: tuple[int, int], **kwargs) -> Layout:
    if form is FormFactor.COMPACT:
        return CompactLayout(window=window, **kwargs)
    return WideLayout(window=window, **kwargs)
