"""Top-down view of the level the player is standing in.

Presentation only: it reads a Session and feeds it input. Every position it
receives is in tile units; converting to pixels happens here and nowhere
else, which is what lets the zoom change without touching the physics.
"""

from __future__ import annotations

import pygame

from ..session import Session
from ..space.tiles import Tile
from .camera import offset_for
from .silhouette import build_silhouette, draw_actor
from .text import TextBlock, TextStyle

BACKGROUND = (10, 9, 12)
TILE_COLORS = {
    Tile.FLOOR: (46, 42, 52),
    Tile.WALL: (74, 68, 82),
    Tile.DOORWAY: (62, 56, 70),
}
FLOOR_LINE = (38, 34, 44)
PORTAL = (188, 156, 96)
PANEL = (16, 14, 19, 232)
HEADING = (226, 196, 140)
BODY = (198, 192, 188)
MUTED = (124, 118, 128)

#: Pixels per tile.
SCALE = 34

PANEL_HEIGHT = 132
MARGIN = 24


class WorldView:
    def __init__(self, session: Session, size: tuple[int, int]) -> None:
        self.session = session
        self.size = size
        self.show_description = True

        self.silhouette = build_silhouette(int(SCALE * 0.95))
        self._panel = pygame.Surface((size[0], PANEL_HEIGHT), pygame.SRCALPHA)

        title_font = pygame.font.SysFont("georgia,serif", 22)
        body_font = pygame.font.SysFont("georgia,serif", 16)
        self.title_style = TextStyle(title_font, HEADING)
        self.body_style = TextStyle(body_font, BODY)
        self.muted_style = TextStyle(body_font, MUTED)

        self.title = TextBlock(self.title_style)
        self.body = TextBlock(self.body_style)

    # -- input ------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
            self.show_description = not self.show_description

    def update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        direction = (
            (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT]),
            (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP]),
        )
        self.session.update(direction, dt)
        self._aim_at_mouse()

    def _aim_at_mouse(self) -> None:
        """Facing follows the cursor, independent of movement."""
        import math

        mx, my = pygame.mouse.get_pos()
        ox, oy = self.camera_offset()
        px, py = self.session.player.position
        dx, dy = mx - (px * SCALE + ox), my - (py * SCALE + oy)
        if (dx, dy) != (0, 0):
            self.session.player.facing = math.atan2(dy, dx)

    # -- camera -----------------------------------------------------------

    def camera_offset(self) -> tuple[float, float]:
        """Frame the room whole if it fits; follow the player if it does not."""
        return offset_for(
            self.session.room_map.size,
            self.session.player.position,
            self.size,
            SCALE,
        )

    # -- drawing ----------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(BACKGROUND)
        offset = self.camera_offset()
        self._draw_tiles(surface, offset)
        self._draw_portals(surface, offset)
        self._draw_player(surface)
        self._draw_panel(surface)

    def _visible_tile_range(self, offset: tuple[float, float]) -> tuple[range, range]:
        """Only the tiles on screen, so map size costs nothing to draw."""
        ox, oy = offset
        first_x = int(-ox // SCALE)
        first_y = int(-oy // SCALE)
        return (
            range(first_x, first_x + self.size[0] // SCALE + 2),
            range(first_y, first_y + self.size[1] // SCALE + 2),
        )

    def _draw_tiles(self, surface: pygame.Surface, offset: tuple[float, float]) -> None:
        tilemap = self.session.room_map.tilemap
        ox, oy = offset
        xs, ys = self._visible_tile_range(offset)
        for ty in ys:
            for tx in xs:
                tile = tilemap.get(tx, ty)
                if tile is Tile.VOID:
                    continue
                rect = pygame.Rect(tx * SCALE + ox, ty * SCALE + oy, SCALE, SCALE)
                pygame.draw.rect(surface, TILE_COLORS[tile], rect)
                if tile is not Tile.WALL:
                    pygame.draw.rect(surface, FLOOR_LINE, rect, width=1)

    def _draw_portals(self, surface: pygame.Surface, offset: tuple[float, float]) -> None:
        ox, oy = offset
        room_portals = self.session.level.portals.get(self.session.player.room_id, {})
        for (tx, ty), _portal in room_portals.items():
            rect = pygame.Rect(tx * SCALE + ox, ty * SCALE + oy, SCALE, SCALE)
            pygame.draw.rect(surface, PORTAL, rect.inflate(-6, -6), width=2, border_radius=3)

    def _draw_player(self, surface: pygame.Surface) -> None:
        """The player is only screen-centred when the camera is following.

        In a framed room the camera is still, so the player must be drawn at
        their actual place in it.
        """
        ox, oy = self.camera_offset()
        px, py = self.session.player.position
        draw_actor(
            surface,
            self.silhouette,
            (px * SCALE + ox, py * SCALE + oy),
            self.session.player.facing,
            SCALE,
        )

    def _draw_panel(self, surface: pygame.Surface) -> None:
        """Room name, prose, and recent log along the bottom.

        Placeholder framing for the text layer -- the real one gets a
        scrolling history buffer rather than a fixed strip.
        """
        room = self.session.room
        if room is None:
            return

        self._panel.fill(PANEL)
        width = self.size[0] - MARGIN * 2

        self.title.width = width
        self.title.text = room.name
        y = self.title.draw(self._panel, MARGIN, 14)

        if self.show_description:
            self.body.width = width
            self.body.text = room.describe(self.session.player)
            self.body.draw(self._panel, MARGIN, y + 6)

        surface.blit(self._panel, (0, self.size[1] - PANEL_HEIGHT))
        self._draw_hint(surface)

    def _draw_hint(self, surface: pygame.Surface) -> None:
        portal = self.session.level.portal_at(
            self.session.player.room_id, self.session.player.position
        )
        hint = portal.label if portal else "WASD to move  ·  mouse to look  ·  Tab hides prose"
        text = self.muted_style.font.render(hint, True, MUTED)
        surface.blit(text, (MARGIN, self.size[1] - PANEL_HEIGHT - 26))
