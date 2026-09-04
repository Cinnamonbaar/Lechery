"""A Pygame-CE view of the current room.

This is presentation only. It reads the World and sends move requests back
to it; it never mutates room state directly. Swapping this out for a
different look should not require touching `lechery.world` at all.
"""

from __future__ import annotations

import pygame

from ..world import World
from .text import TextBlock, TextStyle

BACKGROUND = (18, 16, 20)
PANEL = (28, 25, 32)
HEADING = (226, 196, 140)
BODY = (206, 200, 194)
MUTED = (128, 122, 132)
HOVER = (58, 52, 68)

MARGIN = 32
PADDING = 20
EXIT_HEIGHT = 34


class RoomView:
    """Draws the current room and its exits, and handles clicks on them."""

    def __init__(self, world: World, size: tuple[int, int]) -> None:
        self.world = world
        self.size = size
        self.hovered: int | None = None
        #: (rect, exit key) pairs, rebuilt every frame we draw exits.
        self._exit_hitboxes: list[tuple[pygame.Rect, str]] = []
        self.log: list[str] = []

        title_font = pygame.font.SysFont("georgia,serif", 30)
        body_font = pygame.font.SysFont("georgia,serif", 18)
        small_font = pygame.font.SysFont("georgia,serif", 16)

        self.title_style = TextStyle(title_font, HEADING)
        self.body_style = TextStyle(body_font, BODY)
        self.small_style = TextStyle(small_font, MUTED)

        self.title = TextBlock(self.title_style)
        self.body = TextBlock(self.body_style)
        self.status = TextBlock(self.small_style)

    # -- input ------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self._exit_at(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            index = self._exit_at(event.pos)
            if index is not None:
                self.travel(self._exit_hitboxes[index][1])
        elif event.type == pygame.KEYDOWN:
            key = self._key_for_number(event.key)
            if key is not None:
                self.travel(key)

    def _key_for_number(self, key: int) -> str | None:
        """Number keys 1-9 select the correspondingly listed exit."""
        if pygame.K_1 <= key <= pygame.K_9:
            index = key - pygame.K_1
            if index < len(self._exit_hitboxes):
                return self._exit_hitboxes[index][1]
        return None

    def _exit_at(self, pos: tuple[int, int]) -> int | None:
        for index, (rect, _) in enumerate(self._exit_hitboxes):
            if rect.collidepoint(pos):
                return index
        return None

    def travel(self, key: str) -> None:
        result = self.world.move(key)
        if result.message:
            self.log.append(result.message)
            del self.log[:-4]

    # -- drawing ----------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(BACKGROUND)
        room = self.world.current_room
        if room is None:
            return

        width = surface.get_width()
        text_width = width - MARGIN * 2

        area = self.world.area_of(room)
        self.title.width = text_width
        self.title.text = room.name
        self.body.width = text_width
        self.body.text = room.describe()
        self.status.width = text_width
        self.status.text = area.name if area else ""

        y = MARGIN
        y = self.status.draw(surface, MARGIN, y) + 4
        y = self.title.draw(surface, MARGIN, y) + PADDING
        y = self.body.draw(surface, MARGIN, y) + PADDING * 2

        self._draw_exits(surface, room, y, text_width)
        self._draw_log(surface)

    def _draw_exits(self, surface, room, y: int, width: int) -> None:
        self._exit_hitboxes = []
        exits = room.available_exits()
        if not exits:
            surface.blit(
                self.small_style.font.render("There is no way out.", True, MUTED),
                (MARGIN, y),
            )
            return

        for index, exit_ in enumerate(exits):
            rect = pygame.Rect(MARGIN, y + index * (EXIT_HEIGHT + 6), width, EXIT_HEIGHT)
            self._exit_hitboxes.append((rect, exit_.key_str))
            hovered = self.hovered == index
            pygame.draw.rect(surface, HOVER if hovered else PANEL, rect, border_radius=4)
            label = f"{index + 1}.  {exit_.display_label}"
            text = self.body_style.font.render(label, True, HEADING if hovered else BODY)
            surface.blit(text, (rect.x + 14, rect.centery - text.get_height() // 2))

    def _draw_log(self, surface: pygame.Surface) -> None:
        if not self.log:
            return
        line_height = self.small_style.line_height
        y = surface.get_height() - MARGIN - line_height * len(self.log)
        for index, line in enumerate(self.log):
            surface.blit(
                self.small_style.font.render(line, True, MUTED),
                (MARGIN, y + index * line_height),
            )
