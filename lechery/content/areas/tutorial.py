"""The starter dungeon: generated layout, handcrafted bookends.

The shape shuffles each run so the tutorial is not memorised, but the first
and last rooms are pinned templates -- those two carry the opening beat and
the hand-off to the plains, and neither survives being random.

The prose here is placeholder. It is written to the right length and tone so
layout work can be judged, not to be kept.
"""

from __future__ import annotations

import random

from ...generation import DungeonShape, RoomTemplate, TemplatePool, build_area, generate_dungeon
from ...world import Area, Role

AREA_ID = "tutorial"

SHAPE = DungeonShape(
    critical_path=(6, 8),
    branches=(2, 3),
    branch_length=(1, 2),
    boss_before_exit=True,
    combat_density=0.45,
    treasure_chance=0.8,
)


def template_pool() -> TemplatePool:
    return TemplatePool(
        [
            RoomTemplate(
                id="tut_entrance",
                name="Where You Woke",
                roles=frozenset({Role.ENTRANCE}),
                unique=True,
                tags=frozenset({"indoors", "safe"}),
                descriptions=(
                    "You come to on cold flagstones with no memory of lying "
                    "down on them. The chamber is round, roofless, and open "
                    "to a sky the wrong colour for any hour you remember. "
                    "One passage leads out.",
                ),
            ),
            RoomTemplate(
                id="tut_hall",
                name="Collapsed Hall",
                roles=frozenset({Role.PASSAGE}),
                weight=2.0,
                tags=frozenset({"indoors"}),
                descriptions=(
                    "Pillars stand in two rows, or did; half have come down "
                    "and lie where they fell. Dust hangs in the air as though "
                    "recently disturbed.",
                    "The ceiling has given way at the far end, letting in a "
                    "shaft of pale light and a slow trickle of soil.",
                ),
            ),
            RoomTemplate(
                id="tut_cistern",
                name="Dry Cistern",
                roles=frozenset({Role.PASSAGE, Role.COMBAT}),
                tags=frozenset({"indoors"}),
                descriptions=(
                    "A basin sunk into the floor, empty but for a crust of "
                    "salt and something's shed skin.",
                ),
            ),
            RoomTemplate(
                id="tut_guardroom",
                name="Guardroom",
                roles=frozenset({Role.COMBAT}),
                weight=1.5,
                tags=frozenset({"indoors"}),
                descriptions=(
                    "Racks line the walls, their weapons long since taken. "
                    "Something has made a nest of the straw in the corner.",
                    "Benches, a cold hearth, and four sets of boots left "
                    "neatly by the door. Their owners did not come back for "
                    "them.",
                ),
            ),
            RoomTemplate(
                id="tut_cache",
                name="Storeroom",
                roles=frozenset({Role.TREASURE}),
                tags=frozenset({"indoors"}),
                descriptions=(
                    "Shelves, mostly bare. Mostly.",
                    "A supply room the looters missed, or could not reach. "
                    "One crate remains intact.",
                ),
            ),
            RoomTemplate(
                id="tut_shrine",
                name="Defaced Shrine",
                roles=frozenset({Role.TREASURE, Role.SET_PIECE}),
                unique=True,
                tags=frozenset({"indoors"}),
                descriptions=(
                    "Someone has taken a chisel to every face on the wall "
                    "relief, patiently, one at a time. The offering bowl is "
                    "not empty.",
                ),
            ),
            RoomTemplate(
                id="tut_boss",
                name="The Long Gallery",
                roles=frozenset({Role.BOSS}),
                unique=True,
                tags=frozenset({"indoors"}),
                descriptions=(
                    "The passage opens out into a gallery long enough that "
                    "the far end is dark. Something between you and it "
                    "shifts its weight, and waits.",
                ),
            ),
            RoomTemplate(
                id="tut_gate",
                name="The Broken Gate",
                roles=frozenset({Role.EXIT}),
                unique=True,
                tags=frozenset({"indoors", "safe"}),
                descriptions=(
                    "The doors were torn off their hinges from the inside. "
                    "Past them the tunnel rises, and there is grass growing "
                    "in the seams of the steps -- real grass, real light. "
                    "Whatever this place was, it ends here.",
                ),
            ),
        ]
    )


def build(rng: random.Random) -> Area:
    layout = generate_dungeon(SHAPE, rng, prefix="t")

    # Pin the bookends. The generator guarantees exactly one ENTRANCE and,
    # for a path of any length, one EXIT; a degenerate one-room layout would
    # have neither pinned, which validate() will catch loudly.
    for node in layout.with_role(Role.ENTRANCE):
        node.template_id = "tut_entrance"
    for node in layout.with_role(Role.EXIT):
        node.template_id = "tut_gate"
    for node in layout.with_role(Role.BOSS):
        node.template_id = "tut_boss"

    return build_area(
        layout,
        template_pool(),
        area_id=AREA_ID,
        name="The Undercroft",
        description="Somewhere under the plains, and older than them.",
        rng=rng,
    )
