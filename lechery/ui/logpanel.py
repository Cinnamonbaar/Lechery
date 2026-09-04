"""The log bar: the game's prose, as scrollable history.

Laying out wrapped text costs a measure per candidate line, so entries are
laid out once when they arrive and cached. The panel re-lays-out only when
the log grows or the bar changes width.
"""

from __future__ import annotations

import pygame

from ..log import Entry, Kind, MessageLog
from .panel import PAD, Panel
from .text import TextStyle, wrap

COLORS = {
    Kind.TITLE: (222, 192, 136),
    Kind.PROSE: (188, 182, 178),
    Kind.EVENT: (150, 168, 176),
    Kind.SYSTEM: (120, 114, 126),
}

#: Blank pixels after each entry.
ENTRY_GAP = 10

SCROLLBAR = (70, 64, 78)
SCROLLBAR_TRACK = (32, 29, 37)


class LogPanel(Panel):
    def __init__(self, log: MessageLog, style: TextStyle, tab_style: TextStyle) -> None:
        super().__init__("Log", style, tab_style)
        self.log = log
        self.title_style = TextStyle(
            pygame.font.SysFont("georgia,serif", style.font.get_height() - 1, bold=True),
            COLORS[Kind.TITLE],
        )
        self.body_style = style

        #: Scroll offset in pixels from the bottom. 0 pins to the newest.
        self.scroll = 0
        self._laid_out_width = 0
        self._laid_out_count = 0
        self._lines: list[tuple[str, Kind]] = []

    # -- layout -----------------------------------------------------------

    def _style_for(self, kind: Kind) -> TextStyle:
        return self.title_style if kind is Kind.TITLE else self.body_style

    def _relayout(self, width: int) -> None:
        """Wrap every entry once. Cheap because it only runs when it must."""
        self._lines = []
        for entry in self.log:
            style = self._style_for(entry.kind)
            for line in wrap(self._text_for(entry), style.font, width):
                self._lines.append((line, entry.kind))
            self._lines.append(("", entry.kind))  # the gap after an entry
        self._laid_out_width = width
        self._laid_out_count = len(self.log)

    def _text_for(self, entry: Entry) -> str:
        if entry.kind is Kind.SYSTEM:
            return f"— {entry.text} —"
        return entry.text

    def _ensure_layout(self, width: int) -> None:
        if width != self._laid_out_width or len(self.log) != self._laid_out_count:
            at_bottom = self.scroll == 0
            self._relayout(width)
            if at_bottom:
                # Following the newest text is the default; a player who has
                # scrolled up is left where they were.
                self.scroll = 0

    # -- input ------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> bool:
        consumed = super().handle_event(event)
        if not self.open or not self.rect.collidepoint(pygame.mouse.get_pos()):
            return consumed
        if event.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, self.scroll + event.y * self.body_style.line_height * 3)
            return True
        return consumed

    # -- drawing ----------------------------------------------------------

    def draw_body(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        self._ensure_layout(rect.width)
        line_height = self.body_style.line_height
        visible = rect.height // line_height
        total = len(self._lines)

        # Clamp here rather than on input: the scrollable range depends on
        # the panel height, which input handling does not know.
        max_scroll = max(0, (total - visible) * line_height)
        self.scroll = min(self.scroll, max_scroll)

        first = max(0, total - visible - self.scroll // line_height)
        y = rect.y
        for line, kind in self._lines[first : first + visible]:
            if line:
                style = self._style_for(kind)
                surface.blit(style.font.render(line, True, COLORS[kind]), (rect.x, y))
            y += line_height

        if total > visible:
            self._draw_scrollbar(surface, rect, first, visible, total)

    def _draw_scrollbar(
        self, surface: pygame.Surface, rect: pygame.Rect, first: int, visible: int, total: int
    ) -> None:
        x = rect.right + PAD // 2 - 3
        track = pygame.Rect(x, rect.y, 3, rect.height)
        pygame.draw.rect(surface, SCROLLBAR_TRACK, track)

        height = max(20, int(rect.height * visible / total))
        span = rect.height - height
        offset = 0 if total == visible else int(span * first / (total - visible))
        pygame.draw.rect(surface, SCROLLBAR, pygame.Rect(x, rect.y + offset, 3, height))
