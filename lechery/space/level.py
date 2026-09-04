"""Levels: an Area plus the floorplan of each of its rooms.

The Area answers "what is this room, and what is it for". The Level answers
"what does it look like underfoot, and where are its doors". Keeping them
apart means area content can be authored and tested with no geometry at all.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional

from ..world.area import Area
from ..world.direction import Direction
from .carve import DEFAULT_ROOM_SIZE, Doorway, RoomMap, carve_room


@dataclass(frozen=True)
class Portal:
    """A tile that moves the player elsewhere when stepped on.

    Doorways handle the four compass walls. A portal handles everything that
    is not a wall direction -- a stair up out of the dungeon, a ladder down.
    Without it, an area could be joined logically but not on foot.
    """

    tile: tuple[int, int]
    target_room_id: str
    label: str = ""


@dataclass
class Level:
    area: Area
    maps: dict[str, RoomMap] = field(default_factory=dict)
    #: Portals per room id, keyed by the tile they occupy.
    portals: dict[str, dict[tuple[int, int], Portal]] = field(default_factory=dict)

    @property
    def id(self) -> str:
        return self.area.id

    # -- queries ----------------------------------------------------------

    def map_for(self, room_id: str) -> RoomMap:
        try:
            return self.maps[room_id]
        except KeyError:
            raise KeyError(f"No carved map for room {room_id!r}") from None

    def portal_at(self, room_id: str, position: tuple[float, float]) -> Optional[Portal]:
        return self.portals.get(room_id, {}).get((int(position[0]), int(position[1])))

    def spawn_center(self, room_id: str) -> tuple[float, float]:
        x, y = self.map_for(room_id).center
        return (x + 0.5, y + 0.5)

    def spawn_from(self, room_id: str, arriving_from: Direction) -> tuple[float, float]:
        """Where to stand on entering `room_id` through a given wall.

        `arriving_from` is the direction of travel, so entering while heading
        north means coming in through this room's *south* wall.
        """
        room_map = self.map_for(room_id)
        doorway = room_map.doorways.get(arriving_from.opposite.value)
        if doorway is None:
            return self.spawn_center(room_id)
        x, y = doorway.spawn_tile()
        return (x + 0.5, y + 0.5)

    def add_portal(self, room_id: str, target_room_id: str, label: str = "") -> Portal:
        """Place a portal at the centre of a room."""
        tile = self.map_for(room_id).center
        portal = Portal(tile=tile, target_room_id=target_room_id, label=label)
        self.portals.setdefault(room_id, {})[tile] = portal
        return portal


def build_level(
    area: Area,
    *,
    default_size: tuple[int, int] = DEFAULT_ROOM_SIZE,
    rng: Optional[random.Random] = None,
) -> Level:
    """Carve every room in an area.

    Note this takes only the Area: with rooms carved independently, the
    layout is no longer needed once the exits are wired.
    """
    rng = rng or random.Random()
    level = Level(area=area)
    for room in area:
        level.maps[room.id] = carve_room(room, default_size=default_size, rng=rng)
    return level
