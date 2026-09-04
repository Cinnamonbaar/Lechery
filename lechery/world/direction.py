"""Compass directions used by room exits.

Directions are optional: an exit can be keyed by a `Direction` (a physical
"go north") or by an arbitrary string ("descend", "crawl through the gap").
Keeping both in one keyspace means the UI can render them uniformly.
"""

from __future__ import annotations

from enum import Enum


class Direction(Enum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"
    UP = "up"
    DOWN = "down"
    IN = "in"
    OUT = "out"

    @property
    def opposite(self) -> "Direction":
        return _OPPOSITES[self]

    @property
    def label(self) -> str:
        return self.value.capitalize()

    def __str__(self) -> str:
        return self.value


_OPPOSITES = {
    Direction.NORTH: Direction.SOUTH,
    Direction.SOUTH: Direction.NORTH,
    Direction.EAST: Direction.WEST,
    Direction.WEST: Direction.EAST,
    Direction.UP: Direction.DOWN,
    Direction.DOWN: Direction.UP,
    Direction.IN: Direction.OUT,
    Direction.OUT: Direction.IN,
}


def as_key(value: "Direction | str") -> str:
    """Normalise a direction or free-form exit name into a dict key."""
    if isinstance(value, Direction):
        return value.value
    return value.strip().lower()
