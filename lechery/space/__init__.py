"""Spatial layer: per-room tilemaps, carving, collision.

Geometry, not rendering. Nothing here imports pygame, and positions are in
tile units so the renderer's zoom cannot affect the physics.
"""

from .carve import DEFAULT_ROOM_SIZE, Doorway, RoomMap, carve_room
from .collision import move_and_collide, overlaps_solid
from .level import Level, Portal, build_level
from .tiles import Tile, TileMap

__all__ = [
    "DEFAULT_ROOM_SIZE",
    "Doorway",
    "Level",
    "Portal",
    "RoomMap",
    "Tile",
    "TileMap",
    "build_level",
    "carve_room",
    "move_and_collide",
    "overlaps_solid",
]
