"""The running game: world, floorplans, and the player moving through them.

Everything the UI needs to know lives here, and none of it needs pygame. A
test can spawn a session, walk the player across a dungeon and assert on
where they ended up, at no cost.
"""

from __future__ import annotations

from typing import Optional

from .content.game import START_AREA, new_world
from .entities.actor import Player
from .space import Level
from .world import Room, World


class Session:
    """One playthrough."""

    #: How many log lines to keep. The log is a scratch buffer for the UI,
    #: not a transcript; a real history buffer belongs in the text layer.
    LOG_LIMIT = 6

    def __init__(self, world: World, levels: dict[str, Level], player: Player) -> None:
        self.world = world
        self.levels = levels
        self.player = player
        self.level = levels[START_AREA]
        self.log: list[str] = []

        start = self.world.area(START_AREA).entry_room
        self.player.position = self.level.spawn_in(start.id)
        self._arrive(start.id)

    @classmethod
    def new_game(cls, seed: Optional[int] = None) -> "Session":
        world, levels = new_world(seed)
        return cls(world, levels, Player())

    # -- frame ------------------------------------------------------------

    def update(self, direction: tuple[float, float], dt: float) -> None:
        """Advance one frame. `direction` is raw input, need not be unit."""
        self.player.move(self.level.tilemap, direction, dt)
        self._check_room()
        self._check_portal()

    def _check_room(self) -> None:
        """Fire room hooks when the player crosses into a new room.

        Room transitions are discovered from the tile the player stands on
        rather than from an explicit move command -- which is the whole
        difference between this and a click-an-exit game.
        """
        room_id = self.level.room_id_at(self.player.position)
        if room_id is None or room_id == self.player.room_id:
            return
        self._arrive(room_id)

    def _arrive(self, room_id: str) -> None:
        room = self.world.room(room_id)
        first_time = room_id not in self.player.seen_rooms
        self.player.room_id = room_id
        self.player.seen_rooms.add(room_id)
        self.world.place(room, self.player)
        if first_time and room.name:
            self.say(room.name)

    def _check_portal(self) -> None:
        portal = self.level.portal_at(self.player.position)
        if portal is not None:
            self.travel_to(portal.target_room_id)

    # -- travel -----------------------------------------------------------

    def travel_to(self, room_id: str) -> None:
        """Move the player to another area, or elsewhere in this one."""
        room = self.world.room(room_id)
        if room.area_id is None:
            raise ValueError(f"Room {room_id!r} belongs to no area")

        self.level = self.levels[room.area_id]
        self.player.position = self.level.spawn_in(room_id)
        self._arrive(room_id)
        area = self.world.area_of(room)
        if area is not None:
            self.say(f"-- {area.name} --")

    # -- state ------------------------------------------------------------

    @property
    def room(self) -> Optional[Room]:
        return self.world.current_room

    def say(self, line: str) -> None:
        self.log.append(line)
        del self.log[: -self.LOG_LIMIT]
