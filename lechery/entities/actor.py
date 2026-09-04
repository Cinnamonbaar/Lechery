"""Actors: anything that occupies space and moves through it."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from ..space.collision import move_and_collide
from ..space.tiles import TileMap


@dataclass
class Actor:
    """A body in the world.

    Positions are in tile units, not pixels: the renderer scales. Keeping
    game units independent of the tile pixel size means changing the zoom
    never changes the physics.
    """

    position: tuple[float, float] = (0.0, 0.0)

    #: Half width and half height of the collision box.
    half_extents: tuple[float, float] = (0.3, 0.3)

    #: Tiles per second at full input.
    speed: float = 6.0

    #: Facing, in radians. 0 is east, growing clockwise (screen y is down).
    facing: float = 0.0

    velocity: tuple[float, float] = (0.0, 0.0)

    #: Id of the room the actor is currently standing in, if known.
    room_id: Optional[str] = None

    name: str = "actor"

    def move(self, tilemap: TileMap, direction: tuple[float, float], dt: float) -> bool:
        """Move along `direction` for `dt` seconds. Returns whether it moved.

        `direction` need not be normalised; it is, here, so that holding two
        keys does not grant diagonal speed.
        """
        dx, dy = direction
        magnitude = math.hypot(dx, dy)
        if magnitude == 0.0:
            self.velocity = (0.0, 0.0)
            return False

        dx, dy = dx / magnitude, dy / magnitude
        step = self.speed * dt
        self.velocity = (dx * self.speed, dy * self.speed)
        self.facing = math.atan2(dy, dx)

        before = self.position
        self.position, _ = move_and_collide(
            tilemap, self.position, self.half_extents, (dx * step, dy * step)
        )
        return self.position != before

    @property
    def tile(self) -> tuple[int, int]:
        return (int(self.position[0]), int(self.position[1]))


@dataclass
class Player(Actor):
    """The player character.

    Rendered as an anonymous grey silhouette on the top-down map -- the
    character's actual appearance changes constantly and belongs to the
    paperdoll view, not here. Nothing about appearance lives on this class.
    """

    name: str = "player"
    speed: float = 6.5
    half_extents: tuple[float, float] = (0.28, 0.28)

    #: Rooms the player has stood in, for map drawing and for prose that
    #: should only fire once.
    seen_rooms: set[str] = field(default_factory=set)
