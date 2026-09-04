"""Tests for carving, collision, and the running session. No display needed."""

import random
from collections import deque

import pytest

from lechery.content.areas import plains, tutorial
from lechery.content.game import new_world
from lechery.entities.actor import Actor, Player
from lechery.session import Session
from lechery.space import Tile, TileMap, carve_room, move_and_collide, overlaps_solid
from lechery.ui.camera import offset_for
from lechery.world import Direction as D, Role, Room

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


def a_room(room_id="a:room", size=(21, 15), exits=()):
    room = Room(id=room_id, name="Room", size=size)
    for direction, target in exits:
        room.link(direction, target)
    return room


def test_a_carved_room_is_walled_with_a_walkable_interior():
    room_map = carve_room(a_room())
    tilemap = room_map.tilemap
    assert tilemap.is_solid(0, 0)
    assert tilemap.is_walkable(10, 7)
    assert tilemap.room_at(10, 7) == "a:room"


def test_a_room_gets_one_doorway_per_compass_exit():
    room_map = carve_room(a_room(exits=[(D.NORTH, "a:n"), (D.WEST, "a:w")]))
    assert set(room_map.doorways) == {"north", "west"}
    assert room_map.doorways["north"].target_room_id == "a:n"


def test_non_compass_exits_do_not_become_doorways():
    """An "up" is not a wall; it needs a portal, which the world places."""
    room_map = carve_room(a_room(exits=[(D.UP, "b:elsewhere"), ("crawl", "a:x")]))
    assert room_map.doorways == {}


def test_doorways_are_cut_through_the_wall():
    room_map = carve_room(a_room(exits=[(D.NORTH, "a:n")]))
    door = room_map.doorways["north"]
    assert room_map.tilemap.get(*door.tile) is Tile.DOORWAY
    for cell in door.cells:
        assert room_map.tilemap.is_walkable(*cell)


def test_walking_into_a_doorway_registers_before_the_body_stops():
    """The transition must fire on reaching the threshold.

    A body walking at a doorway grinds to a halt against the void beyond
    it. Detecting the door only once the body has centred on the tile would
    mean the player visibly stops in the gap first.
    """
    room_map = carve_room(a_room(exits=[(D.WEST, "a:w")]))
    half = (0.28, 0.28)
    tilemap = room_map.tilemap
    actor = Actor(position=(5.0, room_map.center[1] + 0.5), speed=30.0, half_extents=half)
    touched_at = None
    for _ in range(120):
        actor.move(tilemap, (-1, 0), 1 / 60)
        if touched_at is None and room_map.doorway_touching(actor.position, half):
            touched_at = actor.position[0]

    assert touched_at is not None, "the doorway was never registered"
    # Registers as the leading edge crosses into the door tile (centre at
    # 1.0 with a 0.28 half-width), not once the centre is over it at 0.5.
    assert touched_at >= 1.0


def test_spawn_tile_is_inside_the_room_not_on_the_threshold():
    room_map = carve_room(a_room(exits=[(D.NORTH, "a:n"), (D.SOUTH, "a:s")]))
    half = (0.28, 0.28)
    for door in room_map.doorways.values():
        x, y = door.spawn_tile()
        assert room_map.tilemap.is_walkable(x, y)
        assert room_map.doorway_touching((x + 0.5, y + 0.5), half) is None


def test_a_room_larger_than_the_default_carves_at_its_authored_size():
    assert carve_room(a_room(size=(49, 33))).size == (49, 33)


# -- camera ---------------------------------------------------------------


def test_a_room_that_fits_is_framed_and_still():
    window, scale = (1024, 720), 34
    small = (27, 17)
    first = offset_for(small, (3.0, 3.0), window, scale)
    second = offset_for(small, (20.0, 12.0), window, scale)
    assert first == second, "camera must not move in a framed room"


def test_a_room_larger_than_the_window_follows_the_player():
    window, scale = (1024, 720), 34
    big = (60, 40)
    near = offset_for(big, (10.0, 20.0), window, scale)
    far = offset_for(big, (40.0, 20.0), window, scale)
    assert far[0] < near[0]


def test_the_camera_never_shows_past_a_large_room_edge():
    window, scale = (1024, 720), 34
    big = (60, 40)
    for pos in [(0.0, 0.0), (59.0, 39.0), (30.0, 20.0)]:
        ox, oy = offset_for(big, pos, window, scale)
        assert ox <= 0 and oy <= 0
        assert ox >= window[0] - big[0] * scale
        assert oy >= window[1] - big[1] * scale


# -- session --------------------------------------------------------------


def test_session_spawns_the_player_in_the_entrance_room():
    session = Session.new_game(1234)
    assert session.room.role is Role.ENTRANCE
    assert session.level.id == tutorial.AREA_ID
    assert not overlaps_solid(
        session.room_map.tilemap, session.player.position, session.player.half_extents
    )


def test_walking_into_a_doorway_moves_the_player_to_the_next_room():
    session = Session.new_game(1234)
    start = session.room.id
    door = next(iter(session.room_map.doorways.values()))

    heading = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}[door.key]
    for _ in range(300):
        session.update(heading, 1 / 60)
        if session.player.room_id != start:
            break

    assert session.player.room_id == door.target_room_id
    assert not overlaps_solid(
        session.room_map.tilemap, session.player.position, session.player.half_extents
    )


def test_arriving_does_not_immediately_bounce_back():
    """Spawning on the far threshold would ping-pong the player forever."""
    session = Session.new_game(1234)
    door = next(iter(session.room_map.doorways.values()))
    session.enter_room(door.target_room_id, arriving_from=door.direction)
    landed = session.player.room_id
    session.update((0, 0), 1 / 60)
    assert session.player.room_id == landed


def test_entering_by_a_wall_puts_the_player_at_the_matching_door():
    session = Session.new_game(1234)
    door = next(iter(session.room_map.doorways.values()))
    target = door.target_room_id
    session.enter_room(target, arriving_from=door.direction)

    back = session.room_map.doorways.get(door.direction.opposite.value)
    assert back is not None, "the return door should exist"
    x, y = session.player.position
    assert abs(x - (back.spawn_tile()[0] + 0.5)) < 1e-6
    assert abs(y - (back.spawn_tile()[1] + 0.5)) < 1e-6


def test_stepping_on_a_portal_moves_the_player_to_the_other_area():
    world, levels = new_world(5)
    session = Session(world, levels, Player())
    dungeon_exit = world.area(tutorial.AREA_ID).first_with_role(Role.EXIT)

    session.travel_to(dungeon_exit.id)  # portals sit at room centre
    session.update((0, 0), 1 / 60)

    assert session.level.id == plains.AREA_ID
    assert session.world.area_of(session.room).id == plains.AREA_ID


@pytest.mark.parametrize("seed", range(8))
def test_every_room_is_reachable_on_foot_through_doorways(seed):
    """Walk the door graph as carved, not the exit graph as authored.

    The layout being connected does not prove the carved rooms are: a
    doorway could fail to be cut, or point at the wrong room.
    """
    world, levels = new_world(seed)
    level = levels[tutorial.AREA_ID]
    start = world.area(tutorial.AREA_ID).entry_room.id

    seen = {start}
    frontier = deque([start])
    while frontier:
        room_id = frontier.popleft()
        for door in level.map_for(room_id).doorways.values():
            if door.target_room_id not in seen:
                seen.add(door.target_room_id)
                frontier.append(door.target_room_id)

    assert seen == set(level.maps), "some rooms cannot be walked to"


@pytest.mark.parametrize("seed", range(8))
def test_every_doorway_has_a_matching_door_coming_back(seed):
    """A one-way door would strand the player; exits are made in pairs."""
    world, levels = new_world(seed)
    for level in levels.values():
        for room_id, room_map in level.maps.items():
            for door in room_map.doorways.values():
                back = level.map_for(door.target_room_id).doorways.get(
                    door.direction.opposite.value
                )
                assert back is not None and back.target_room_id == room_id


@pytest.mark.parametrize("seed", range(8))
def test_both_ends_of_every_portal_are_standable(seed):
    world, levels = new_world(seed)
    for level in levels.values():
        for room_id, portals in level.portals.items():
            for portal in portals.values():
                assert level.map_for(room_id).tilemap.is_walkable(*portal.tile)
                target = world.room(portal.target_room_id)
                other = levels[target.area_id]
                assert other.map_for(target.id).tilemap.is_walkable(
                    *other.map_for(target.id).center
                )
