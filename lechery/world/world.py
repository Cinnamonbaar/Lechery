"""The World: the room registry and the movement rules that act on it."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, Optional

from .area import Area
from .direction import Direction
from .exits import Exit
from .room import Room


@dataclass
class MoveResult:
    """The outcome of an attempted move.

    Returned rather than raised because a refused move is ordinary gameplay,
    not an error: the UI wants a message to print either way.
    """

    ok: bool
    message: str = ""
    room: Optional[Room] = None
    previous: Optional[Room] = None
    exit: Optional[Exit] = field(default=None, repr=False)

    def __bool__(self) -> bool:
        return self.ok


class World:
    """Owns every area and room, and is the only thing that moves an actor.

    Rooms hold ids rather than object references, so this class is what turns
    an id into a room. That indirection is what lets content modules define
    rooms in any order and reference each other freely.
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        #: The master seed every area's layout was derived from. Kept on the
        #: world so a save file can record it and rebuild the same map.
        self.seed = seed
        self.areas: dict[str, Area] = {}
        self._rooms: dict[str, Room] = {}
        self.current_room: Optional[Room] = None

    # -- registration -----------------------------------------------------

    def add_area(self, area: Area) -> Area:
        if area.id in self.areas:
            raise ValueError(f"Duplicate area id {area.id!r}")
        self.areas[area.id] = area
        for room in area:
            self._register_room(room)
        return area

    def _register_room(self, room: Room) -> None:
        if room.id in self._rooms:
            raise ValueError(f"Duplicate room id {room.id!r}")
        self._rooms[room.id] = room

    # -- lookup -----------------------------------------------------------

    def room(self, room_id: str) -> Room:
        try:
            return self._rooms[room_id]
        except KeyError:
            raise KeyError(f"No room registered with id {room_id!r}") from None

    def area(self, area_id: str) -> Area:
        try:
            return self.areas[area_id]
        except KeyError:
            raise KeyError(f"No area registered with id {area_id!r}") from None

    def area_of(self, room: Room) -> Optional[Area]:
        if room.area_id is None:
            return None
        return self.areas.get(room.area_id)

    @property
    def rooms(self) -> Iterator[Room]:
        return iter(self._rooms.values())

    def __contains__(self, room_id: object) -> bool:
        return room_id in self._rooms

    # -- movement ---------------------------------------------------------

    def place(self, room: "Room | str", actor: object = None) -> MoveResult:
        """Put the actor in a room directly, ignoring exits.

        For starting the game, teleports, and scripted scene changes.
        """
        destination = self.room(room) if isinstance(room, str) else room
        previous = self.current_room
        if previous is not None:
            previous.leave(actor)
        self.current_room = destination
        destination.enter(actor)
        return MoveResult(True, room=destination, previous=previous)

    def move(self, key: Direction | str, actor: object = None) -> MoveResult:
        """Attempt to travel from the current room along `key`."""
        origin = self.current_room
        if origin is None:
            return MoveResult(False, "You are nowhere.")

        exit_ = origin.exit_for(key)
        if exit_ is None:
            return MoveResult(False, "You can't go that way.")

        if not exit_.is_open(actor):
            return MoveResult(False, exit_.blocked_message, exit=exit_)

        if exit_.target not in self:
            raise KeyError(
                f"Exit {exit_.key_str!r} from room {origin.id!r} points at "
                f"unregistered room {exit_.target!r}"
            )

        destination = exit_.destination(self)
        origin.leave(actor)
        self.current_room = destination
        destination.enter(actor)
        return MoveResult(
            True,
            f"You go {exit_.display_label.lower()}.",
            room=destination,
            previous=origin,
            exit=exit_,
        )

    # -- integrity --------------------------------------------------------

    def validate(self) -> list[str]:
        """Report structural problems in the map.

        Cheap to run on startup and in tests; catches the failure mode this
        design invites, which is an exit naming a room id that never got
        registered (a typo, or a content module that was not imported).
        """
        problems: list[str] = []
        for room in self.rooms:
            for exit_ in room.exits.values():
                if exit_.target not in self:
                    problems.append(
                        f"{room.id}: exit {exit_.key_str!r} -> unknown room "
                        f"{exit_.target!r}"
                    )
                elif exit_.target == room.id:
                    problems.append(f"{room.id}: exit {exit_.key_str!r} leads to itself")
        for area in self.areas.values():
            if area.entry_room_id is not None and area.entry_room_id not in area.rooms:
                problems.append(
                    f"{area.id}: entry room {area.entry_room_id!r} is not in the area"
                )
        return problems
