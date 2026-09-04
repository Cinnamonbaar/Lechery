"""Top-down view of the level the player is standing in.

Presentation only: it reads a Session and feeds it input. Every position it
receives is in tile units; converting to pixels happens here and nowhere
else, which is what lets the zoom change without touching the physics.
"""

from __future__ import annotations

import math

import pygame

from ..session import Session
from ..space.tiles import Tile
from .camera import offset_for
from .fonts import load as load_font
from .silhouette import build_silhouette, draw_actor
from .text import TextStyle

BACKGROUND = (10, 9, 12)
TILE_COLORS = {
    Tile.FLOOR: (46, 42, 52),
    Tile.WALL: (74, 68, 82),
    Tile.DOORWAY: (62, 56, 70),
}
FLOOR_LINE = (38, 34, 44)
PORTAL = (188, 156, 96)
MUTED = (124, 118, 128)

#: Pixels per tile.
SCALE = 34

MARGIN = 18


class WorldView:
    def __init__(self, session: Session, rect: pygame.Rect) -> None:
        self.session = session
        #: The centre pane. Reassigned whenever the bars collapse, so the
        #: camera re-frames the room instead of sliding it off-centre.
        self.rect = rect

        self.silhouette = build_silhouette(int(SCALE * 0.95))
        self.muted_style = TextStyle(load_font("body", 15), MUTED)

    # -- input ------------------------------------------------------------

    def update(self, direction: tuple[float, float], dt: float, aim_at_mouse: bool = True) -> None:
        self.session.update(direction, dt)
        if aim_at_mouse:
            self._aim_at_mouse()
        elif direction != (0.0, 0.0):
            # Without a cursor, the body faces where it is going.
            self.session.player.facing = math.atan2(direction[1], direction[0])

    def _aim_at_mouse(self) -> None:
        """Facing follows the cursor, independent of movement."""
        mx, my = pygame.mouse.get_pos()
        ox, oy = self.camera_offset()
        px, py = self.session.player.position
        dx = mx - (self.rect.x + px * SCALE + ox)
        dy = my - (self.rect.y + py * SCALE + oy)
        if (dx, dy) != (0, 0):
            self.session.player.facing = math.atan2(dy, dx)

    # -- camera -----------------------------------------------------------

    def camera_offset(self) -> tuple[float, float]:
        """Frame the room whole if it fits; follow the player if it does not."""
        return offset_for(
            self.session.room_map.size,
            self.session.player.position,
            self.rect.size,
            SCALE,
        )

    # -- drawing ----------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        """Draw into this view's rect.

        A subsurface is used rather than offsetting every blit: it clips
        for free, so a room larger than the pane cannot bleed over the bars.
        """
        if self.rect.width <= 0 or self.rect.height <= 0:
            return
        pane = surface.subsurface(self.rect.clip(surface.get_rect()))
        pane.fill(BACKGROUND)

        offset = self.camera_offset()
        self._draw_tiles(pane, offset)
        self._draw_portals(pane, offset)
        self._draw_player(pane)
        self._draw_hint(pane)

    def _visible_tile_range(self, offset: tuple[float, float]) -> tuple[range, range]:
        """Only the tiles on screen, so map size costs nothing to draw."""
        ox, oy = offset
        first_x = int(-ox // SCALE)
        first_y = int(-oy // SCALE)
        return (
            range(first_x, first_x + self.rect.width // SCALE + 2),
            range(first_y, first_y + self.rect.height // SCALE + 2),
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

    def _draw_hint(self, surface: pygame.Surface) -> None:
        portal = self.session.level.portal_at(
            self.session.player.room_id, self.session.player.position
        )
        hint = portal.label if portal else "WASD move  ·  mouse look  ·  [ ] toggle bars"
        text = self.muted_style.font.render(hint, True, MUTED)
        surface.blit(text, (MARGIN, surface.get_height() - MARGIN - text.get_height()))
