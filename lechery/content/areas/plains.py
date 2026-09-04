"""The plains: the hub. Fully handcrafted, same pipeline as the dungeon.

Every node here pins a template and every position is chosen by hand, so the
"generator" does no generating -- it just dresses and wires. That is the
point: the hub gets the builder's exit-wiring and id-namespacing for free
without inheriting any randomness.

Later areas branch off the crossroads. Keeping the hub small and its exits
explicit is what makes adding a spoke a two-line change.
"""

from __future__ import annotations

import random

from ...generation import Layout, Node, RoomTemplate, TemplatePool, build_area
from ...world import Area, Role

AREA_ID = "plains"

#: (node id, grid position, role, template id)
PLACES = [
    ("undergate", (0, 2), Role.ENTRANCE, "plains_undergate"),
    ("crossroads", (0, 1), Role.PASSAGE, "plains_crossroads"),
    ("road_west", (-1, 1), Role.PASSAGE, "plains_road"),
    ("gate", (0, 0), Role.PASSAGE, "plains_gate"),
    ("square", (1, 0), Role.HAVEN, "town_square"),
]

#: Undirected edges between the places above.
ROADS = [
    ("undergate", "crossroads"),
    ("crossroads", "road_west"),
    ("crossroads", "gate"),
    ("gate", "square"),
]


def template_pool() -> TemplatePool:
    return TemplatePool(
        [
            RoomTemplate(
                id="plains_undergate",
                name="The Sunken Door",
                roles=frozenset({Role.ENTRANCE}),
                tags=frozenset({"outdoors", "safe"}),
                descriptions=(
                    "You come up out of the dark into grass to your knees and "
                    "a sky that goes on without interruption in every "
                    "direction. Behind you the stair drops back down into the "
                    "hill. Ahead the land is flat, and green, and enormous.",
                ),
            ),
            RoomTemplate(
                id="plains_crossroads",
                name="The Crossroads",
                size=(37, 23),
                tags=frozenset({"outdoors", "safe"}),
                descriptions=(
                    "Two cart tracks meet in the grass and a leaning post "
                    "marks the spot, its signboards long since taken for "
                    "firewood. North stands a walled town. The western road "
                    "runs off toward nothing you can make out from here.",
                ),
            ),
            RoomTemplate(
                id="plains_road",
                name="The Western Road",
                tags=frozenset({"outdoors"}),
                descriptions=(
                    "The track thins to a footpath and then to an idea of a "
                    "footpath. Whatever is out this way, it is further than "
                    "one day's walk.",
                ),
            ),
            RoomTemplate(
                id="plains_gate",
                name="Town Gate",
                tags=frozenset({"outdoors", "safe"}),
                descriptions=(
                    "The wall is high, well kept, and manned -- the first "
                    "evidence you have seen that anyone in this place expects "
                    "to be here tomorrow. The gate stands open.",
                ),
            ),
            RoomTemplate(
                id="town_square",
                name="Market Square",
                roles=frozenset({Role.HAVEN}),
                # Larger than the screen on purpose: the town is where the
                # camera stops framing a room and starts following the
                # player. Everything else about it carves identically.
                size=(49, 33),
                tags=frozenset({"indoors", "safe", "town"}),
                descriptions=(
                    "Stalls, a well, and a good deal of noise. People here "
                    "look at you the way people look at weather coming in "
                    "off the plain: with interest, and no particular alarm.",
                ),
            ),
        ]
    )


def layout() -> Layout:
    hub = Layout()
    for node_id, position, role, template_id in PLACES:
        hub.add(Node(id=node_id, position=position, role=role, template_id=template_id))
    for a, b in ROADS:
        hub.connect(a, b)
    return hub


def build(rng: random.Random) -> tuple[Area, Layout]:
    hub = layout()
    area = build_area(
        hub,
        template_pool(),
        area_id=AREA_ID,
        name="The Plains",
        description="Open country, and the town that sits in the middle of it.",
        rng=rng,
    )
    return area, hub
