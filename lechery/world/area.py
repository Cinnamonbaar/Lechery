"""Areas: named regions that own a set of rooms."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, Optional

from .roles import Role

from .room import Room


@dataclass
class Area:
    """A region of the map.

    Areas exist so that region-wide properties have somewhere to live --
    ambient track, encounter table, danger rating, a corruption modifier --
    without every room carrying a copy. None of those exist yet; what an Area
    holds today is a name, a set of rooms, and an entry point.
    """

    id: str
    name: str
    description: str = ""

    #: Rooms keyed by room id, in insertion order.
    rooms: dict[str, Room] = field(default_factory=dict, repr=False)

    #: Room the player arrives at when entering the area from elsewhere.
    entry_room_id: Optional[str] = None

    tags: set[str] = field(default_factory=set)

    def add(self, room: Room) -> Room:
        """Adopt a room into this area."""
        if room.id in self.rooms:
            raise ValueError(f"Area {self.id!r} already has a room {room.id!r}")
        room.area_id = self.id
        self.rooms[room.id] = room
        # An explicit ENTRANCE always wins; otherwise the first room added
        # is the entry point, which is right for small handmade areas.
        if self.entry_room_id is None or room.role is Role.ENTRANCE:
            self.entry_room_id = room.id
        return room

    def make_room(self, room_id: str, name: str, description: str = "", **kwargs) -> Room:
        """Construct a plain Room and adopt it in one call."""
        return self.add(Room(id=room_id, name=name, description=description, **kwargs))

    def room(self, room_id: str) -> Room:
        try:
            return self.rooms[room_id]
        except KeyError:
            raise KeyError(f"No room {room_id!r} in area {self.id!r}") from None

    def rooms_with_role(self, role: Role) -> list[Room]:
        """Every room in the area serving `role`.

        This is how the rest of the game addresses a generated area: an exit
        room has no stable id when the layout is random, but it always has a
        role.
        """
        return [room for room in self.rooms.values() if room.role is role]

    def first_with_role(self, role: Role) -> Optional[Room]:
        for room in self.rooms.values():
            if room.role is role:
                return room
        return None

    @property
    def entry_room(self) -> Optional[Room]:
        if self.entry_room_id is None:
            return None
        return self.rooms[self.entry_room_id]

    def __iter__(self) -> Iterator[Room]:
        return iter(self.rooms.values())

    def __len__(self) -> int:
        return len(self.rooms)

    def __str__(self) -> str:
        return self.name
