"""Tilemaps: the walkable geometry of an area.

Pure Python, like the rest of the model -- a tilemap is geometry, not
rendering. The renderer reads it; so does collision; so do tests.
"""

from __future__ import annotations

from enum import IntEnum
from typing import Iterator, Optional


class Tile(IntEnum):
    #: Outside the level. Solid, and drawn as nothing.
    VOID = 0
    FLOOR = 1
    WALL = 2
    #: Walkable, but marks the threshold between two rooms.
    DOORWAY = 3
    #: Walkable. Springs an effect the first time it is stood on, then
    #: spends itself and becomes plain floor.
    TRAP = 4

    @property
    def solid(self) -> bool:
        return self in (Tile.VOID, Tile.WALL)


class TileMap:
    """A rectangular grid of tiles, with a room id recorded per tile.

    The per-tile room id is what lets the game answer "which room is the
    player standing in" every frame without any geometry tests -- one array
    lookup. That question drives room descriptions, encounters and music, so
    it needs to be cheap.
    """

    def __init__(self, width: int, height: int, fill: Tile = Tile.VOID) -> None:
        self.width = width
        self.height = height
        self._tiles = [fill] * (width * height)
        self._rooms: list[Optional[str]] = [None] * (width * height)

    # -- access -----------------------------------------------------------

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get(self, x: int, y: int) -> Tile:
        """Out-of-bounds reads return VOID, so callers need no bounds check."""
        if not self.in_bounds(x, y):
            return Tile.VOID
        return self._tiles[y * self.width + x]

    def set(self, x: int, y: int, tile: Tile, room_id: Optional[str] = None) -> None:
        if not self.in_bounds(x, y):
            return
        index = y * self.width + x
        self._tiles[index] = tile
        if room_id is not None:
            self._rooms[index] = room_id

    def room_at(self, x: int, y: int) -> Optional[str]:
        if not self.in_bounds(x, y):
            return None
        return self._rooms[y * self.width + x]

    def is_solid(self, x: int, y: int) -> bool:
        return self.get(x, y).solid

    def is_walkable(self, x: int, y: int) -> bool:
        return not self.get(x, y).solid

    # -- bulk operations --------------------------------------------------

    def fill_rect(
        self, x: int, y: int, width: int, height: int, tile: Tile, room_id: Optional[str] = None
    ) -> None:
        for ty in range(y, y + height):
            for tx in range(x, x + width):
                self.set(tx, ty, tile, room_id)

    def outline_rect(
        self, x: int, y: int, width: int, height: int, tile: Tile, room_id: Optional[str] = None
    ) -> None:
        for tx in range(x, x + width):
            self.set(tx, y, tile, room_id)
            self.set(tx, y + height - 1, tile, room_id)
        for ty in range(y, y + height):
            self.set(x, ty, tile, room_id)
            self.set(x + width - 1, ty, tile, room_id)

    def walkable_tiles(self) -> Iterator[tuple[int, int]]:
        for y in range(self.height):
            for x in range(self.width):
                if self.is_walkable(x, y):
                    yield (x, y)

    def count(self, tile: Tile) -> int:
        return self._tiles.count(tile)

    def __str__(self) -> str:
        glyphs = {
            Tile.VOID: " ", Tile.FLOOR: ".", Tile.WALL: "#",
            Tile.DOORWAY: "+", Tile.TRAP: "^",
        }
        return "\n".join(
            "".join(glyphs[self.get(x, y)] for x in range(self.width))
            for y in range(self.height)
        )
