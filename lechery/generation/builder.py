"""Turning a Layout plus a TemplatePool into a real Area."""

from __future__ import annotations

import random
from typing import Optional

from ..world.area import Area
from ..world.roles import Role
from .layout import Layout, direction_between


def build_area(
    layout: Layout,
    pool,
    *,
    area_id: str,
    name: str,
    description: str = "",
    rng: Optional[random.Random] = None,
) -> Area:
    """Dress every node in `layout` with a room and wire up the exits.

    Room ids are namespaced with the area id (`tutorial:n3`) so that two
    generated areas cannot collide in the World's global room registry.
    """
    rng = rng or random.Random()
    pool.reset()
    area = Area(id=area_id, name=name, description=description)

    for node in layout:
        template = (
            pool.get(node.template_id)
            if node.template_id is not None
            else pool.pick(node.role, rng)
        )
        room = template.build(f"{area_id}:{node.id}", node.role, rng)
        room.position = node.position
        area.add(room)

    for node in layout:
        room = area.room(f"{area_id}:{node.id}")
        for neighbour in layout.neighbours(node):
            direction = direction_between(node.position, neighbour.position)
            if direction is None:
                raise ValueError(
                    f"Nodes {node.id!r} and {neighbour.id!r} are linked but not "
                    f"adjacent; layout.validate() would have caught this"
                )
            # Each node writes only its own outgoing exit; the neighbour
            # writes the return leg when its own turn comes.
            room.link(direction, f"{area_id}:{neighbour.id}")

    entrance = layout.with_role(Role.ENTRANCE)
    if entrance:
        area.entry_room_id = f"{area_id}:{entrance[0].id}"
    return area
