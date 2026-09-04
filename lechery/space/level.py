"""Levels: an Area plus the floorplan it was carved into.

The Area answers "what is this room, and what is it for". The Level answers
"where is it, and can I walk there". Keeping them apart means area content
can be authored and tested without any geometry at all.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional

from ..generation.layout import Layout
from ..world.area import Area
from .carve import CarveStyle, RoomBlock, carve
from .tiles import TileMap


@dataclass(frozen=True)
class Portal:
    """A tile that moves the player to another area when stepped on.

    Cross-area travel needs a physical thing to walk into now that exits are
    not buttons. A portal is that thing: the stair up out of the dungeon, the
    town gate. It carries a destination room id, which the World resolves.
    """

    tile: tuple[int, int]
    target_room_id: str
    label: str = ""


@dataclass
class Level:
    area: Area
    tilemap: TileMap
    blocks: dict[str, RoomBlock] = field(default_factory=dict)
    portals: dict[tuple[int, int], Portal] = field(default_factory=dict)

    @property
    def id(self) -> str:
        return self.area.id

    # -- queries ----------------------------------------------------------

    def room_id_at(self, position: tuple[float, float]) -> Optional[str]:
        return self.tilemap.room_at(int(position[0]), int(position[1]))

    def portal_at(self, position: tuple[float, float]) -> Optional[Portal]:
        return self.portals.get((int(position[0]), int(position[1])))

    def spawn_in(self, room_id: str) -> tuple[float, float]:
        """A walkable point at the centre of a room, in world units."""
        block = self.blocks[room_id]
        x, y = block.center
        return (x + 0.5, y + 0.5)

    def add_portal(self, room_id: str, target_room_id: str, label: str = "") -> Portal:
        """Place a portal at the centre of `room_id`."""
        tile = self.blocks[room_id].center
        portal = Portal(tile=tile, target_room_id=target_room_id, label=label)
        self.portals[tile] = portal
        return portal


def build_level(
    area: Area,
    layout: Layout,
    *,
    style: Optional[CarveStyle] = None,
    rng: Optional[random.Random] = None,
) -> Level:
    tilemap, node_blocks = carve(layout, area_id=area.id, style=style, rng=rng)
    blocks = {block.room_id: block for block in node_blocks.values()}
    return Level(area=area, tilemap=tilemap, blocks=blocks)
