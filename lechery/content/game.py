"""Assembling a new game world.

Area *content* lives in `lechery.content.areas`; this module owns the world
map -- which areas exist and how they join. When a new area branches off the
hub it is registered here and nowhere else.
"""

from __future__ import annotations

import random
from typing import Optional

from ..generation import rng_for
from ..world import Direction as D, Role, World
from .areas import plains, tutorial


def new_game(seed: Optional[int] = None) -> World:
    """Build a fresh world. The same seed always yields the same map."""
    if seed is None:
        seed = random.randrange(2**31)

    world = World(seed=seed)
    world.add_area(tutorial.build(rng_for(seed, tutorial.AREA_ID)))
    world.add_area(plains.build(rng_for(seed, plains.AREA_ID)))

    _join_areas(world)

    problems = world.validate()
    if problems:
        raise RuntimeError(
            "generated an invalid world (seed %d):\n  %s" % (seed, "\n  ".join(problems))
        )

    world.place(world.area(tutorial.AREA_ID).entry_room)
    return world


def _join_areas(world: World) -> None:
    """Stitch the area graph together.

    Areas are joined by role rather than by room id, because a generated
    area's exit room has a different id every run. This is the whole reason
    Role exists.
    """
    dungeon_exit = world.area(tutorial.AREA_ID).first_with_role(Role.EXIT)
    hub_entrance = world.area(plains.AREA_ID).entry_room
    if dungeon_exit is None or hub_entrance is None:
        raise RuntimeError("the starter dungeon and the hub must both be reachable")

    dungeon_exit.connect(
        D.UP,
        hub_entrance,
        label="Climb toward the light",
    )
