"""World model: geography, and the rules for moving through it.

This package imports no pygame and knows nothing about rendering. It is the
authority on where things are; the presentation layer only reads it.
"""

from .area import Area
from .direction import Direction
from .exits import Exit
from .room import Room
from .world import MoveResult, World

__all__ = ["Area", "Direction", "Exit", "MoveResult", "Room", "World"]
