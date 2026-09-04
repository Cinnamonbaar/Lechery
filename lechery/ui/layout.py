"""The three-pane screen: paperdoll, world, log.

Only the centre pane is load-bearing for play, so the side bars collapse
into thin tabs rather than disappearing -- a bar with no handle is a bar the
player cannot get back. The centre takes whatever space is left, and the
world view measures itself against that rect rather than the window, so
collapsing a bar re-frames the room instead of sliding it off-centre.
"""

from __future__ import annotations

from dataclasses import dataclass

import pygame

#: Width of a bar when open.
BAR_WIDTH = 268

#: Width of the tab left behind when a bar is collapsed.
TAB_WIDTH = 22

#: The centre pane never shrinks below this; bars give way first.
MIN_CENTER = 420


@dataclass
class ScreenLayout:
    """Computes the three pane rects for a window size and collapse state."""

    window: tuple[int, int]
    left_open: bool = True
    right_open: bool = True

    def _bar_widths(self) -> tuple[int, int]:
        left = BAR_WIDTH if self.left_open else TAB_WIDTH
        right = BAR_WIDTH if self.right_open else TAB_WIDTH

        # A narrow window shrinks the bars rather than the play area; both
        # give way together so the centre stays centred.
        overflow = (left + right + MIN_CENTER) - self.window[0]
        if overflow > 0:
            if self.left_open and self.right_open:
                left -= overflow // 2
                right -= overflow - overflow // 2
            elif self.left_open:
                left -= overflow
            elif self.right_open:
                right -= overflow
            left = max(left, TAB_WIDTH)
            right = max(right, TAB_WIDTH)
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

    def toggle_left(self) -> None:
        self.left_open = not self.left_open

    def toggle_right(self) -> None:
        self.right_open = not self.right_open
