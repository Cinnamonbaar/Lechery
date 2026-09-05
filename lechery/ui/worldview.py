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
from .metrics import px
from .silhouette import build_silhouette, draw_actor
from .text import TextStyle

BACKGROUND = (10, 9, 12)
TRAP_MARK = (150, 96, 128)
TILE_COLORS = {
    Tile.FLOOR: (46, 42, 52),
    Tile.WALL: (74, 68, 82),
    Tile.DOORWAY: (62, 56, 70),
    Tile.TRAP: (46, 42, 52),  # reads as floor; the mark on top gives it away
}
FLOOR_LINE = (38, 34, 44)
PORTAL = (188, 156, 96)
MUTED = (124, 118, 128)

#: Design units per tile. Larger than the room count is small, so a room
#: fills the screen and the player pawn reads big rather than distant.
TILE = 52

MARGIN = 18


def tile_px() -> int:
    """Device pixels per tile, at the current display scale."""
    return px(TILE)


class WorldView:
    def __init__(self, session: Session, rect: pygame.Rect) -> None:
        self.session = session
        #: The centre pane. Reassigned whenever the bars collapse, so the
        #: camera re-frames the room instead of sliding it off-centre.
        self.rect = rect

        self._silhouette_scale = 0
        self.silhouette = None
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
        world_x, world_y = self.session.player.position
        dx = mx - (self.rect.x + world_x * tile_px() + ox)
        dy = my - (self.rect.y + world_y * tile_px() + oy)
        if (dx, dy) != (0, 0):
            self.session.player.facing = math.atan2(dy, dx)

    # -- camera -----------------------------------------------------------

    def camera_offset(self) -> tuple[float, float]:
        """Frame the room whole if it fits; follow the player if it does not."""
        return offset_for(
            self.session.room_map.size,
            self.session.player.position,
            self.rect.size,
            tile_px(),
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
        first_x = int(-ox // tile_px())
        first_y = int(-oy // tile_px())
        return (
            range(first_x, first_x + self.rect.width // tile_px() + 2),
            range(first_y, first_y + self.rect.height // tile_px() + 2),
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
                rect = pygame.Rect(tx * tile_px() + ox, ty * tile_px() + oy, tile_px(), tile_px())
                pygame.draw.rect(surface, TILE_COLORS[tile], rect)
                if tile is not Tile.WALL:
                    pygame.draw.rect(surface, FLOOR_LINE, rect, width=px(1))
                if tile is Tile.TRAP:
                    # A faint plate, so it is noticeable without being an
                    # obvious "do not step here" the way a bright tile would.
                    pygame.draw.rect(
                        surface, TRAP_MARK, rect.inflate(-px(10), -px(10)),
                        width=px(2), border_radius=px(2),
                    )

    def _draw_portals(self, surface: pygame.Surface, offset: tuple[float, float]) -> None:
        ox, oy = offset
        room_portals = self.session.level.portals.get(self.session.player.room_id, {})
        for (tx, ty), _portal in room_portals.items():
            rect = pygame.Rect(tx * tile_px() + ox, ty * tile_px() + oy, tile_px(), tile_px())
            pygame.draw.rect(surface, PORTAL, rect.inflate(-px(6), -px(6)), width=px(2), border_radius=px(3))

    def _player_silhouette(self) -> pygame.Surface:
        """The body sprite, rebuilt only when the display scale changes.

        Rotating it every frame is cheap; redrawing it every frame is not.
        """
        size = int(tile_px() * 0.95)
        if self.silhouette is None or size != self._silhouette_scale:
            self.silhouette = build_silhouette(size)
            self._silhouette_scale = size
        return self.silhouette

    def _draw_player(self, surface: pygame.Surface) -> None:
        """The player is only screen-centred when the camera is following.

        In a framed room the camera is still, so the player must be drawn at
        their actual place in it.
        """
        ox, oy = self.camera_offset()
        world_x, world_y = self.session.player.position
        draw_actor(
            surface,
            self._player_silhouette(),
            (world_x * tile_px() + ox, world_y * tile_px() + oy),
            self.session.player.facing,
            tile_px(),
        )

    def _draw_hint(self, surface: pygame.Surface) -> None:
        portal = self.session.level.portal_at(
            self.session.player.room_id, self.session.player.position
        )
        hint = portal.label if portal else "WASD move  ·  mouse look  ·  [ ] toggle bars"
        text = self.muted_style.font.render(hint, True, MUTED)
        surface.blit(
            text, (px(MARGIN), surface.get_height() - px(MARGIN) - text.get_height())
        )
