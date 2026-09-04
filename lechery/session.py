"""The running game: world, floorplans, and the player moving through them.

Everything the UI needs lives here, and none of it needs pygame. A test can
spawn a session, walk the player through a dungeon and assert on where they
ended up, at no cost.
"""

from __future__ import annotations

from typing import Optional

from .content.game import START_AREA, new_world
from .entities.actor import Player
from .log import Kind, MessageLog
from .narration import describe_change
from .space import Level, RoomMap
from .world import Direction, Room, World


class Session:
    """One playthrough."""

    def __init__(self, world: World, levels: dict[str, Level], player: Player) -> None:
        self.world = world
        self.levels = levels
        self.player = player
        self.level = levels[START_AREA]
        self.log = MessageLog()

        # Transformations narrate themselves wherever they are triggered
        # from, rather than every caller remembering to log.
        self.player.character.traits.on_change = self._narrate_change

        start = self.world.area(START_AREA).entry_room
        self._arrive(start.id)
        self.player.position = self.level.spawn_center(start.id)

    @classmethod
    def new_game(cls, seed: Optional[int] = None) -> "Session":
        world, levels = new_world(seed)
        return cls(world, levels, Player())

    # -- frame ------------------------------------------------------------

    @property
    def room_map(self) -> RoomMap:
        return self.level.map_for(self.player.room_id)

    def update(self, direction: tuple[float, float], dt: float) -> None:
        """Advance one frame. `direction` is raw input, need not be unit."""
        self.player.move(self.room_map.tilemap, direction, dt)
        self._check_doorway()
        self._check_portal()

    def _check_doorway(self) -> None:
        """Transition when the player stands in a doorway.

        Doorways are walkable, so the player crosses the threshold and is
        moved; they never get stuck standing in one, because the far side
        spawns them inset from the matching door.
        """
        doorway = self.room_map.doorway_touching(
            self.player.position, self.player.half_extents
        )
        if doorway is None:
            return
        self.enter_room(doorway.target_room_id, arriving_from=doorway.direction)

    def _check_portal(self) -> None:
        portal = self.level.portal_at(self.player.room_id, self.player.position)
        if portal is not None:
            self.travel_to(portal.target_room_id)

    # -- travel -----------------------------------------------------------

    def enter_room(self, room_id: str, arriving_from: Optional[Direction] = None) -> None:
        """Walk into an adjoining room in the same area."""
        self._arrive(room_id)
        self.player.position = (
            self.level.spawn_from(room_id, arriving_from)
            if arriving_from is not None
            else self.level.spawn_center(room_id)
        )

    def travel_to(self, room_id: str) -> None:
        """Move to a room in another area, via a portal or a script."""
        room = self.world.room(room_id)
        if room.area_id is None:
            raise ValueError(f"Room {room_id!r} belongs to no area")

        changed_area = room.area_id != self.level.id
        if changed_area:
            area = self.world.area_of(room)
            if area is not None:
                self.log.system(area.name)
        self.level = self.levels[room.area_id]
        self._arrive(room_id)
        self.player.position = self.level.spawn_center(room_id)

    def _arrive(self, room_id: str) -> None:
        """Enter a room, and narrate it.

        The name is logged every time, so scrollback reads as a route. The
        prose only on a first visit: repeating a paragraph the player has
        already read trains them to stop reading the log at all.
        """
        room = self.world.room(room_id)
        first_time = room_id not in self.player.seen_rooms
        self.player.room_id = room_id
        self.player.seen_rooms.add(room_id)
        self.world.place(room, self.player)

        if room.name:
            self.log.title(room.name)
        if first_time:
            description = room.describe(self.player)
            if description:
                self.log.prose(description)

    def _narrate_change(self, change) -> None:
        line = describe_change(change, self.player.character)
        if line:
            self.log.add(line, Kind.EVENT)

    # -- state ------------------------------------------------------------

    @property
    def room(self) -> Optional[Room]:
        return self.world.current_room

    def say(self, line: str, kind: Kind = Kind.EVENT) -> None:
        self.log.add(line, kind)
