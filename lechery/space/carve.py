"""Carving a Layout into a walkable TileMap.

Each layout node becomes a rectangular block of floor, placed at its grid
position times a fixed pitch. Linked nodes get a corridor punched through the
gap between them. Because the layout is a tree of grid-adjacent nodes, the
blocks never overlap and the corridors are always axis-aligned -- the two
properties that make this carver short enough to trust.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional

from ..generation.layout import Layout, Node
from .tiles import Tile, TileMap


@dataclass(frozen=True)
class CarveStyle:
    """Tile dimensions of the carved floorplan."""

    #: Interior size of a room block, excluding its wall ring.
    room_size: tuple[int, int] = (13, 11)

    #: Variation in interior size, so rooms are not uniform.
    size_jitter: int = 4

    #: Tiles of dead space between adjacent room blocks; the corridor runs
    #: through it. Two, because one leaves rooms sharing a wall and reads as
    #: a single large room rather than two.
    gap: int = 5

    #: Width of the corridor and its doorway.
    door_width: int = 3

    #: Border of VOID kept around the whole map.
    margin: int = 1

    @property
    def pitch(self) -> tuple[int, int]:
        """Distance between the origins of two adjacent room blocks."""
        return (
            self.room_size[0] + 2 + self.gap,
            self.room_size[1] + 2 + self.gap,
        )


@dataclass
class RoomBlock:
    """Where one layout node ended up in tile space."""

    node_id: str
    room_id: str
    #: Interior rect, excluding walls: (x, y, width, height).
    rect: tuple[int, int, int, int]

    @property
    def center(self) -> tuple[int, int]:
        x, y, w, h = self.rect
        return (x + w // 2, y + h // 2)

    def contains(self, x: int, y: int) -> bool:
        rx, ry, rw, rh = self.rect
        return rx <= x < rx + rw and ry <= y < ry + rh


def carve(
    layout: Layout,
    *,
    area_id: str,
    style: Optional[CarveStyle] = None,
    rng: Optional[random.Random] = None,
) -> tuple[TileMap, dict[str, RoomBlock]]:
    """Build a tilemap for `layout`. Returns the map and its room blocks."""
    style = style or CarveStyle()
    rng = rng or random.Random()

    min_x, min_y, max_x, max_y = layout.bounds
    pitch_x, pitch_y = style.pitch
    # The last column and row need no trailing gap, hence the subtraction;
    # without it every map carries a strip of dead space on two sides.
    width = (max_x - min_x + 1) * pitch_x - style.gap + style.margin * 2
    height = (max_y - min_y + 1) * pitch_y - style.gap + style.margin * 2
    tilemap = TileMap(width, height)

    blocks: dict[str, RoomBlock] = {}
    for node in layout:
        blocks[node.id] = _carve_room(tilemap, node, area_id, style, rng, (min_x, min_y))

    # Corridors are carved after every room, so a corridor can safely punch
    # through a wall that a later room would otherwise have drawn back in.
    carved: set[frozenset[str]] = set()
    for node in layout:
        for neighbour in layout.neighbours(node):
            edge = frozenset({node.id, neighbour.id})
            if edge in carved:
                continue
            carved.add(edge)
            _carve_corridor(tilemap, blocks[node.id], blocks[neighbour.id], area_id, style)

    return tilemap, blocks


def _carve_room(
    tilemap: TileMap,
    node: Node,
    area_id: str,
    style: CarveStyle,
    rng: random.Random,
    origin: tuple[int, int],
) -> RoomBlock:
    pitch_x, pitch_y = style.pitch
    base_x = (node.position[0] - origin[0]) * pitch_x + style.margin
    base_y = (node.position[1] - origin[1]) * pitch_y + style.margin

    # Jitter shrinks a room from its maximum and re-centres it in its cell,
    # so blocks stay inside their pitch and corridors still line up.
    max_w, max_h = style.room_size
    width = max_w - rng.randrange(0, style.size_jitter + 1)
    height = max_h - rng.randrange(0, style.size_jitter + 1)
    x = base_x + 1 + (max_w - width) // 2
    y = base_y + 1 + (max_h - height) // 2

    room_id = f"{area_id}:{node.id}"
    tilemap.outline_rect(x - 1, y - 1, width + 2, height + 2, Tile.WALL, room_id)
    tilemap.fill_rect(x, y, width, height, Tile.FLOOR, room_id)
    return RoomBlock(node_id=node.id, room_id=room_id, rect=(x, y, width, height))


def _carve_corridor(
    tilemap: TileMap,
    a: RoomBlock,
    b: RoomBlock,
    area_id: str,
    style: CarveStyle,
) -> None:
    """Punch an L-free straight corridor between two adjacent blocks.

    The blocks are grid neighbours, so they are either side by side or one
    above the other; the corridor runs along the axis they differ on, at the
    midpoint of their overlap on the other axis.
    """
    ax, ay, aw, ah = a.rect
    bx, by, bw, bh = b.rect
    half = style.door_width // 2

    if ax + aw <= bx or bx + bw <= ax:  # horizontally separated
        left, right = (a, b) if ax < bx else (b, a)
        lx, ly, lw, lh = left.rect
        rx, ry, rw, rh = right.rect
        # Centre the corridor on the rooms' shared vertical span.
        low = max(ly, ry)
        high = min(ly + lh, ry + rh)
        centre = (low + high) // 2
        for x in range(lx + lw - 1, rx + 1):
            for offset in range(-half, half + 1):
                tile = Tile.DOORWAY if x in (lx + lw - 1, rx) else Tile.FLOOR
                room = left.room_id if x < (lx + lw + rx) // 2 else right.room_id
                tilemap.set(x, centre + offset, tile, room)
        _wall_around_corridor(tilemap, range(lx + lw - 1, rx + 1), centre, half, area_id, horizontal=True)
    else:  # vertically separated
        top, bottom = (a, b) if ay < by else (b, a)
        tx, ty, tw, th = top.rect
        bx2, by2, bw2, bh2 = bottom.rect
        low = max(tx, bx2)
        high = min(tx + tw, bx2 + bw2)
        centre = (low + high) // 2
        for y in range(ty + th - 1, by2 + 1):
            for offset in range(-half, half + 1):
                tile = Tile.DOORWAY if y in (ty + th - 1, by2) else Tile.FLOOR
                room = top.room_id if y < (ty + th + by2) // 2 else bottom.room_id
                tilemap.set(centre + offset, y, tile, room)
        _wall_around_corridor(tilemap, range(ty + th - 1, by2 + 1), centre, half, area_id, horizontal=False)


def _wall_around_corridor(
    tilemap: TileMap,
    span: range,
    centre: int,
    half: int,
    area_id: str,
    *,
    horizontal: bool,
) -> None:
    """Line the corridor so it does not open onto the void."""
    for along in span:
        for side in (-half - 1, half + 1):
            x, y = (along, centre + side) if horizontal else (centre + side, along)
            if tilemap.get(x, y) is Tile.VOID:
                tilemap.set(x, y, Tile.WALL)
