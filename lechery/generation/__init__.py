"""Procedural generation: layouts, content pools, and the builder between them.

The pipeline is deliberately three stages, because each is useful without the
others: a Layout can be tested for connectivity with no content, a
TemplatePool can be authored with no layout, and a handcrafted area is just a
layout whose nodes all pin a template.
"""

from .builder import build_area
from .dungeon import DungeonShape, generate_dungeon
from .layout import Layout, Node, direction_between
from .seeding import derive_seed, rng_for
from .templates import RoomTemplate, TemplatePool

__all__ = [
    "DungeonShape",
    "Layout",
    "Node",
    "RoomTemplate",
    "TemplatePool",
    "build_area",
    "derive_seed",
    "direction_between",
    "generate_dungeon",
    "rng_for",
]
