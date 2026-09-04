"""Assembling a new game world.

Area *content* lives in `lechery.content.areas`; this module owns the world
map -- which areas exist, how they join, and where the portals between them
sit. When a new area branches off the hub it is registered here and nowhere
else.
"""

from __future__ import annotations

import random
from typing import Optional

from ..generation import rng_for
from ..space import Level, build_level
from ..world import Direction as D, Role, World
from .areas import plains, tutorial

AREA_MODULES = (tutorial, plains)

#: Where a new game begins.
START_AREA = tutorial.AREA_ID


def new_world(seed: Optional[int] = None) -> tuple[World, dict[str, Level]]:
    """Build a fresh world and its floorplans.

    The same seed always yields the same map, layout and carving alike.
    """
    if seed is None:
        seed = random.randrange(2**31)

    world = World(seed=seed)
    levels: dict[str, Level] = {}

    for module in AREA_MODULES:
        area, layout = module.build(rng_for(seed, module.AREA_ID))
        world.add_area(area)
        # A separate stream for carving, so tuning room sizes cannot
        # reshuffle which rooms the layout generated.
        levels[area.id] = build_level(
            area, layout, rng=rng_for(seed, f"{module.AREA_ID}:carve")
        )

    _join_areas(world, levels)

    problems = world.validate()
    if problems:
        raise RuntimeError(
            "generated an invalid world (seed %d):\n  %s" % (seed, "\n  ".join(problems))
        )
    return world, levels


def _join_areas(world: World, levels: dict[str, Level]) -> None:
    """Stitch the area graph together, in the model and in space.

    Areas are joined by role rather than by room id, because a generated
    area's exit room has a different id every run. The logical exit and the
    portal are created together: a link the player cannot physically reach
    is worse than no link at all.
    """
    dungeon_exit = world.area(tutorial.AREA_ID).first_with_role(Role.EXIT)
    hub_entrance = world.area(plains.AREA_ID).entry_room
    if dungeon_exit is None or hub_entrance is None:
        raise RuntimeError("the starter dungeon and the hub must both be reachable")

    dungeon_exit.connect(D.UP, hub_entrance, label="Climb toward the light")
    levels[tutorial.AREA_ID].add_portal(
        dungeon_exit.id, hub_entrance.id, label="Climb toward the light"
    )
    levels[plains.AREA_ID].add_portal(
        hub_entrance.id, dungeon_exit.id, label="Back down into the dark"
    )
