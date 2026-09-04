"""Spatial layer: tilemaps, carving, collision.

Geometry, not rendering. Nothing here imports pygame, and positions are in
tile units so the renderer's zoom cannot affect the physics.
"""

from .carve import CarveStyle, RoomBlock, carve
from .collision import move_and_collide, overlaps_solid
from .level import Level, Portal, build_level
from .tiles import Tile, TileMap

__all__ = [
    "CarveStyle",
    "Level",
    "Portal",
    "RoomBlock",
    "Tile",
    "TileMap",
    "build_level",
    "carve",
    "move_and_collide",
    "overlaps_solid",
]
