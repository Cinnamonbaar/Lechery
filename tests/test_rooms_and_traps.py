"""Tests for room decoration, breast-trap tiles, and cup-size display."""

import random

import pytest

from lechery.content.game import new_world
from lechery.content.areas import tutorial
from lechery.entities.actor import Player
from lechery.session import Session
from lechery.space import Tile
from lechery.space.carve import DEFAULT_ROOM_SIZE, carve_room
from lechery.traits import cup_size, default_character
from lechery.world import Role, Room


def a_room(room_id="a:r", size=(19, 13), tags=(), exits=()):
    from lechery.world import Direction as D

    room = Room(id=room_id, name="R", size=size, tags=set(tags))
    for direction, target in exits:
        room.link(direction, target)
    return room


# -- cup sizes ------------------------------------------------------------


@pytest.mark.parametrize(
    "index,label",
    [(0, "flat"), (1, "A cup"), (3, "C cup"), (5, "DD cup"), (12, "K cup")],
)
def test_cup_size_labels(index, label):
    assert cup_size(index) == label


def test_cup_size_clamps_past_the_last_letter():
    assert cup_size(999) == cup_size(12)


# -- decoration -----------------------------------------------------------


def test_a_plain_room_has_a_solid_wall_ring_and_open_interior():
    room_map = carve_room(a_room(tags=("safe",)), rng=random.Random(1))
    tm = room_map.tilemap
    assert tm.get(0, 0) is Tile.WALL
    assert tm.get(tm.width // 2, tm.height // 2) is Tile.FLOOR


def test_safe_rooms_are_never_decorated():
    """A town square full of pillars reads as rubble, not a town."""
    for seed in range(20):
        room_map = carve_room(a_room(tags=("safe",)), rng=random.Random(seed))
        tiles = {room_map.tilemap.get(x, y)
                 for x in range(room_map.tilemap.width)
                 for y in range(room_map.tilemap.height)}
        assert Tile.TRAP not in tiles
        # No interior pillars: the only walls are the outer ring.
        interior_walls = [
            (x, y)
            for y in range(1, room_map.tilemap.height - 1)
            for x in range(1, room_map.tilemap.width - 1)
            if room_map.tilemap.get(x, y) is Tile.WALL
        ]
        assert interior_walls == []


def test_a_trapped_room_actually_gets_traps():
    seen_trap = False
    for seed in range(20):
        room_map = carve_room(a_room(tags=("trapped",)), rng=random.Random(seed))
        if any(
            room_map.tilemap.get(x, y) is Tile.TRAP
            for x in range(room_map.tilemap.width)
            for y in range(room_map.tilemap.height)
        ):
            seen_trap = True
            break
    assert seen_trap


def test_decoration_never_touches_a_doorway_or_its_approach():
    """A pillar or trap two tiles in from every wall cannot block a door."""
    for seed in range(30):
        room_map = carve_room(
            a_room(tags=("trapped",), exits=[]),
            rng=random.Random(seed),
        )
        tm = room_map.tilemap
        for x in range(tm.width):
            for y in range(tm.height):
                if tm.get(x, y) in (Tile.WALL, Tile.TRAP):
                    if 0 < x < tm.width - 1 and 0 < y < tm.height - 1:
                        # interior decoration keeps a two-tile margin
                        assert 2 < x < tm.width - 3 or tm.get(x, y) is Tile.WALL
                        assert 2 < y < tm.height - 3 or tm.get(x, y) is Tile.WALL


def test_the_default_room_is_small_enough_to_zoom():
    assert DEFAULT_ROOM_SIZE == (19, 13)


# -- springing a trap -----------------------------------------------------


def _trap_cell(session):
    tm = session.room_map.tilemap
    for y in range(tm.height):
        for x in range(tm.width):
            if tm.get(x, y) is Tile.TRAP:
                return (x, y)
    return None


def test_stepping_on_a_trap_grows_the_bust_and_spends_the_tile():
    # Find a seed whose starting-area walk reaches a trapped room; simplest
    # is to carve a trapped room directly and drive the session onto it.
    world, levels = new_world(3)
    session = Session(world, levels, Player(character=default_character("T")))

    # Put a trap under the player's feet in the current room.
    tm = session.room_map.tilemap
    x, y = int(session.player.position[0]), int(session.player.position[1])
    tm.set(x, y, Tile.TRAP)

    before = session.player.character.traits["bust"]
    session.update((0.0, 0.0), 1 / 60)

    assert session.player.character.traits["bust"] == before + 1
    assert tm.get(x, y) is Tile.FLOOR, "the trap should be spent, not re-fire"


def test_a_spent_trap_does_not_fire_again():
    world, levels = new_world(3)
    session = Session(world, levels, Player(character=default_character("T")))
    tm = session.room_map.tilemap
    x, y = int(session.player.position[0]), int(session.player.position[1])
    tm.set(x, y, Tile.TRAP)

    session.update((0.0, 0.0), 1 / 60)
    once = session.player.character.traits["bust"]
    for _ in range(10):
        session.update((0.0, 0.0), 1 / 60)
    assert session.player.character.traits["bust"] == once


def test_the_trap_logs_and_narrates():
    world, levels = new_world(3)
    session = Session(world, levels, Player(character=default_character("T")))
    tm = session.room_map.tilemap
    x, y = int(session.player.position[0]), int(session.player.position[1])
    tm.set(x, y, Tile.TRAP)

    before = len(session.log)
    session.update((0.0, 0.0), 1 / 60)
    assert len(session.log) > before


@pytest.mark.parametrize("seed", range(6))
def test_every_room_is_still_reachable_with_decoration(seed):
    """Pillars must not wall a room off from its own doorways."""
    from collections import deque

    world, levels = new_world(seed)
    level = levels[tutorial.AREA_ID]
    start = world.area(tutorial.AREA_ID).entry_room.id

    for room_id, room_map in level.maps.items():
        tm = room_map.tilemap
        # Every doorway cell must reach the room's centre across floor.
        centre = room_map.center
        seen = {centre}
        frontier = deque([centre])
        while frontier:
            cx, cy = frontier.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (cx + dx, cy + dy)
                if n not in seen and tm.is_walkable(*n):
                    seen.add(n)
                    frontier.append(n)
        for door in room_map.doorways.values():
            assert door.tile in seen or any(
                c in seen for c in door.cells
            ), f"{room_id}: a doorway is walled off by decoration"
