"""Carving one room into its own tilemap.

Each room is a screen. A room's map is a walled rectangle with a doorway cut
into each wall that faces a neighbour, so the map's shape is decided entirely
by the room's size and which exits it has -- nothing about a room's map
depends on where its neighbours ended up, which is what makes rooms
independent enough to generate lazily later.

Rooms that fit the view are framed whole; rooms larger than it scroll. That
is one carver, not two: the difference lives in the room's authored size.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional

from ..world.direction import Direction, as_key
from ..world.room import Room
from .tiles import Tile, TileMap

#: Tile size of a room that fills one screen, walls included.
DEFAULT_ROOM_SIZE = (27, 17)

#: Compass directions can be cut into a wall; anything else (an "up", a
#: "scramble down") is not a wall direction and becomes a portal instead.
WALL_DIRECTIONS = (Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST)


@dataclass(frozen=True)
class Doorway:
    """A gap in a room's wall leading to another room."""

    direction: Direction
    #: The threshold tile at the centre of the gap, in room tile space.
    tile: tuple[int, int]
    target_room_id: str
    #: Every tile of the gap. A doorway triggers on a body *overlapping*
    #: one of these rather than centring on it, so the transition fires as
    #: the player reaches the threshold instead of after they have pressed
    #: into the void beyond it.
    cells: tuple[tuple[int, int], ...] = ()
    width: int = 3

    @property
    def key(self) -> str:
        return self.direction.value

    def spawn_tile(self, inset: int = 2) -> tuple[int, int]:
        """Where an arriving player stands: inside the room, off the door.

        Landing on the threshold itself would re-trigger the transition and
        bounce the player back where they came from.
        """
        x, y = self.tile
        dx, dy = _INWARD[self.direction]
        return (x + dx * inset, y + dy * inset)


#: Which way is "into the room" from a doorway in each wall.
_INWARD = {
    Direction.NORTH: (0, 1),
    Direction.SOUTH: (0, -1),
    Direction.EAST: (-1, 0),
    Direction.WEST: (1, 0),
}


@dataclass
class RoomMap:
    """One room's floorplan."""

    room_id: str
    tilemap: TileMap
    doorways: dict[str, Doorway]

    @property
    def size(self) -> tuple[int, int]:
        return (self.tilemap.width, self.tilemap.height)

    @property
    def center(self) -> tuple[int, int]:
        return (self.tilemap.width // 2, self.tilemap.height // 2)

    def doorway_touching(
        self, position: tuple[float, float], half_extents: tuple[float, float]
    ) -> Optional[Doorway]:
        """The doorway a body at `position` is standing in, if any.

        Overlap rather than containment, so the transition fires the moment
        the player reaches the threshold rather than once their centre is
        over it -- the room beyond is not carved into this map, so pressing
        further just grinds against the void.
        """
        x, y = position
        hx, hy = half_extents
        left, right = int(x - hx), int(x + hx)
        top, bottom = int(y - hy), int(y + hy)
        for doorway in self.doorways.values():
            for cx, cy in doorway.cells:
                if left <= cx <= right and top <= cy <= bottom:
                    return doorway
        return None


def carve_room(
    room: Room,
    *,
    default_size: tuple[int, int] = DEFAULT_ROOM_SIZE,
    door_width: int = 3,
    rng: Optional[random.Random] = None,
) -> RoomMap:
    """Build the tilemap for a single room, doorways and all."""
    rng = rng or random.Random()
    width, height = room.size or default_size

    tilemap = TileMap(width, height, Tile.VOID)
    tilemap.fill_rect(1, 1, width - 2, height - 2, Tile.FLOOR, room.id)
    tilemap.outline_rect(0, 0, width, height, Tile.WALL, room.id)

    doorways: dict[str, Doorway] = {}
    for direction in WALL_DIRECTIONS:
        exit_ = room.exit_for(direction)
        if exit_ is None:
            continue
        doorway = _cut_doorway(tilemap, direction, exit_.target, door_width, room.id)
        doorways[as_key(direction)] = doorway

    return RoomMap(room_id=room.id, tilemap=tilemap, doorways=doorways)


def _cut_doorway(
    tilemap: TileMap,
    direction: Direction,
    target_room_id: str,
    width: int,
    room_id: str,
) -> Doorway:
    """Cut a gap of `width` tiles into the middle of one wall."""
    half = width // 2
    mid_x = tilemap.width // 2
    mid_y = tilemap.height // 2

    if direction is Direction.NORTH:
        tile = (mid_x, 0)
        cells = [(mid_x + offset, 0) for offset in range(-half, half + 1)]
    elif direction is Direction.SOUTH:
        tile = (mid_x, tilemap.height - 1)
        cells = [(mid_x + offset, tilemap.height - 1) for offset in range(-half, half + 1)]
    elif direction is Direction.WEST:
        tile = (0, mid_y)
        cells = [(0, mid_y + offset) for offset in range(-half, half + 1)]
    else:
        tile = (tilemap.width - 1, mid_y)
        cells = [(tilemap.width - 1, mid_y + offset) for offset in range(-half, half + 1)]

    for x, y in cells:
        tilemap.set(x, y, Tile.DOORWAY, room_id)

    return Doorway(
        direction=direction,
        tile=tile,
        target_room_id=target_room_id,
        cells=tuple(cells),
        width=width,
    )
