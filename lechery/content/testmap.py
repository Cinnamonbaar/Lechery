"""A throwaway map used to exercise the world model.

Deliberately generic: none of this is setting or lore, it exists so the
systems have something to move through until the real content is designed.
Delete it freely.
"""

from __future__ import annotations

from ..world import Area, Direction as D, Room, World


def build_world() -> World:
    world = World()

    hollow = Area(
        id="hollow",
        name="The Hollow",
        description="A shallow basin of scrub and standing water.",
    )

    clearing = hollow.make_room(
        "clearing",
        "Overgrown Clearing",
        "Grass grows waist-high here, flattened in a rough circle as though "
        "something large sleeps in it nightly. Paths lead off in three "
        "directions.",
    ).tag("outdoors", "safe")

    creek = hollow.make_room(
        "creek",
        "Shallow Creek",
        "Cold water runs ankle-deep over pale stones. The far bank is steep "
        "and root-tangled.",
    ).tag("outdoors", "water")

    hollow.make_room(
        "thicket",
        "Bramble Thicket",
        "Thorns close overhead until the light goes green and dim. Something "
        "has torn a low tunnel through the undergrowth.",
    ).tag("outdoors")

    stair = hollow.make_room(
        "stair",
        "Sunken Stair",
        "Steps of fitted stone descend into the earth, far older than the "
        "wood above them. Cold air rises from below.",
    ).tag("outdoors")

    clearing.connect(D.NORTH, creek)
    clearing.connect(D.EAST, hollow.room("thicket"))
    clearing.connect(D.WEST, stair)

    # An asymmetric passage: you can slide down the bank, not climb back.
    creek.link("scramble down", "cellar", label="Scramble down the bank")

    undercroft = Area(
        id="undercroft",
        name="The Undercroft",
        description="Cut stone beneath the hollow, and older than it.",
    )

    cellar = undercroft.make_room(
        "cellar",
        "Flooded Cellar",
        "Black water laps at the walls of a room that was never meant to hold "
        "it. A doorway gapes to the south.",
    ).tag("indoors", "water")

    vault = undercroft.make_room(
        "vault",
        "Sealed Vault",
        "The air here is dry and utterly still. Whatever this room was built "
        "to keep, it kept.",
    ).tag("indoors")

    undercroft.entry_room_id = "cellar"

    stair.connect(D.DOWN, cellar)
    cellar.link(D.SOUTH, vault, hidden=True, label="A seam in the masonry")
    vault.link(D.NORTH, cellar)

    world.add_area(hollow)
    world.add_area(undercroft)
    world.place(clearing)
    return world
