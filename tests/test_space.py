"""Tests for carving, collision, and the running session. No display needed."""

import random
from collections import deque

import pytest

from lechery.content.areas import plains, tutorial
from lechery.content.game import new_world
from lechery.entities.actor import Actor, Player
from lechery.generation import DungeonShape, generate_dungeon
from lechery.session import Session
from lechery.space import Tile, TileMap, carve, move_and_collide, overlaps_solid
from lechery.world import Role

SEEDS = list(range(12))


def open_map(width=10, height=10):
    """A walled box of floor."""
    tilemap = TileMap(width, height, Tile.FLOOR)
    tilemap.outline_rect(0, 0, width, height, Tile.WALL)
    return tilemap


# -- tilemap --------------------------------------------------------------


def test_out_of_bounds_reads_as_solid_void():
    tilemap = open_map()
    assert tilemap.get(-1, 5) is Tile.VOID
    assert tilemap.is_solid(-1, 5)
    assert tilemap.is_solid(999, 999)


def test_tiles_remember_their_room():
    tilemap = TileMap(4, 4)
    tilemap.fill_rect(0, 0, 2, 2, Tile.FLOOR, "area:kitchen")
    assert tilemap.room_at(1, 1) == "area:kitchen"
    assert tilemap.room_at(3, 3) is None


# -- collision ------------------------------------------------------------


def test_a_body_stops_at_a_wall_instead_of_passing_through():
    tilemap = open_map()
    position, hit = move_and_collide(tilemap, (2.0, 5.0), (0.3, 0.3), (-50.0, 0.0))
    assert hit.x
    assert position[0] > 1.0  # outside the wall at x=0
    assert not overlaps_solid(tilemap, position, (0.3, 0.3))


def test_a_blocked_diagonal_slides_along_the_wall():
    """The reason collision is resolved one axis at a time."""
    tilemap = open_map()
    start = (1.5, 5.0)
    position, hit = move_and_collide(tilemap, start, (0.3, 0.3), (-1.0, 1.0))
    assert hit.x
    assert position[1] > start[1]  # movement continued on the free axis


def test_an_unobstructed_move_is_exact():
    tilemap = open_map()
    position, hit = move_and_collide(tilemap, (5.0, 5.0), (0.3, 0.3), (0.25, -0.5))
    assert position == (5.25, 4.5)
    assert not hit.any


@pytest.mark.parametrize("direction", [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1)])
def test_a_body_can_never_leave_a_sealed_room(direction):
    """Hammer each direction; the box must stay walkable throughout."""
    tilemap = open_map()
    actor = Actor(position=(5.0, 5.0), speed=40.0)
    for _ in range(400):
        actor.move(tilemap, direction, 1 / 60)
        assert not overlaps_solid(tilemap, actor.position, actor.half_extents)


def test_diagonal_movement_is_not_faster_than_straight():
    tilemap = open_map(60, 60)
    straight = Actor(position=(5.0, 5.0))
    diagonal = Actor(position=(5.0, 5.0))
    for _ in range(30):
        straight.move(tilemap, (1, 0), 1 / 60)
        diagonal.move(tilemap, (1, 1), 1 / 60)
    travelled_straight = straight.position[0] - 5.0
    travelled_diagonal = ((diagonal.position[0] - 5.0) ** 2 + (diagonal.position[1] - 5.0) ** 2) ** 0.5
    assert travelled_diagonal == pytest.approx(travelled_straight, rel=1e-6)


def test_zero_input_does_not_move_or_turn():
    tilemap = open_map()
    actor = Actor(position=(5.0, 5.0), facing=1.0)
    assert not actor.move(tilemap, (0, 0), 1 / 60)
    assert actor.position == (5.0, 5.0)
    assert actor.facing == 1.0


# -- carving --------------------------------------------------------------


@pytest.mark.parametrize("seed", SEEDS)
def test_every_carved_room_is_walkable_and_tagged(seed):
    layout = generate_dungeon(rng=random.Random(seed))
    tilemap, blocks = carve(layout, area_id="t", rng=random.Random(seed))
    for block in blocks.values():
        x, y = block.center
        assert tilemap.is_walkable(x, y)
        assert tilemap.room_at(x, y) is not None


@pytest.mark.parametrize("seed", SEEDS)
def test_the_whole_carved_floorplan_is_one_connected_space(seed):
    """A carved map must be walkable end to end, or a room is stranded.

    The layout being connected does not prove the tilemap is: a corridor can
    fail to punch through. This walks the actual floor tiles.
    """
    layout = generate_dungeon(rng=random.Random(seed))
    tilemap, blocks = carve(layout, area_id="t", rng=random.Random(seed))

    start = next(iter(blocks.values())).center
    seen = {start}
    frontier = deque([start])
    while frontier:
        x, y = frontier.popleft()
        for step in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            neighbour = (x + step[0], y + step[1])
            if neighbour not in seen and tilemap.is_walkable(*neighbour):
                seen.add(neighbour)
                frontier.append(neighbour)

    for block in blocks.values():
        assert block.center in seen, f"{block.room_id} is walled off"


@pytest.mark.parametrize("seed", SEEDS)
def test_rooms_never_overlap_in_tile_space(seed):
    layout = generate_dungeon(rng=random.Random(seed))
    _, blocks = carve(layout, area_id="t", rng=random.Random(seed))
    claimed: set[tuple[int, int]] = set()
    for block in blocks.values():
        x, y, w, h = block.rect
        cells = {(cx, cy) for cy in range(y, y + h) for cx in range(x, x + w)}
        assert not (cells & claimed), f"{block.room_id} overlaps another room"
        claimed |= cells


def test_carving_is_deterministic_for_a_seed():
    layout = generate_dungeon(rng=random.Random(4))
    first, _ = carve(layout, area_id="t", rng=random.Random(4))
    second, _ = carve(layout, area_id="t", rng=random.Random(4))
    assert str(first) == str(second)


def test_a_single_room_layout_carves_cleanly():
    layout = generate_dungeon(DungeonShape(critical_path=(1, 1), branches=(0, 0)), random.Random(0))
    tilemap, blocks = carve(layout, area_id="t", rng=random.Random(0))
    assert len(blocks) == 1
    assert tilemap.count(Tile.FLOOR) > 0


# -- session --------------------------------------------------------------


def test_session_spawns_the_player_in_the_entrance_room():
    session = Session.new_game(1234)
    assert session.room.role is Role.ENTRANCE
    assert session.level.id == tutorial.AREA_ID
    assert not overlaps_solid(
        session.level.tilemap, session.player.position, session.player.half_extents
    )


def test_walking_into_the_next_room_fires_the_room_change():
    session = Session.new_game(1234)
    start = session.room.id
    for _ in range(150):
        session.update((-1, 0), 1 / 60)
    assert session.player.room_id != start
    assert session.room.id == session.player.room_id


def test_stepping_on_a_portal_moves_the_player_to_the_other_area():
    world, levels = new_world(5)
    session = Session(world, levels, Player())
    dungeon_exit = world.area(tutorial.AREA_ID).first_with_role(Role.EXIT)

    session.travel_to(dungeon_exit.id)  # stands on the portal tile
    session.update((0, 0), 1 / 60)

    assert session.level.id == plains.AREA_ID
    assert session.world.area_of(session.room).id == plains.AREA_ID


@pytest.mark.parametrize("seed", range(6))
def test_the_player_can_physically_walk_the_whole_dungeon(seed):
    """Reachability in tile space, not just in the room graph.

    The generator guarantees a connected layout, but a bad carve could still
    seal a room off. This is the check that would catch it.
    """
    world, levels = new_world(seed)
    level = levels[tutorial.AREA_ID]
    tilemap = level.tilemap
    start = level.blocks[world.area(tutorial.AREA_ID).entry_room.id].center

    seen = {start}
    frontier = deque([start])
    while frontier:
        x, y = frontier.popleft()
        for step in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            neighbour = (x + step[0], y + step[1])
            if neighbour not in seen and tilemap.is_walkable(*neighbour):
                seen.add(neighbour)
                frontier.append(neighbour)

    for room_id, block in level.blocks.items():
        assert block.center in seen, f"{room_id} cannot be reached on foot"


@pytest.mark.parametrize("seed", range(6))
def test_both_ends_of_every_portal_are_standable(seed):
    world, levels = new_world(seed)
    for level in levels.values():
        for portal in level.portals.values():
            assert level.tilemap.is_walkable(*portal.tile)
            target = world.room(portal.target_room_id)
            other = levels[target.area_id]
            assert other.tilemap.is_walkable(*other.blocks[target.id].center)
