"""Tests for the world model. No pygame, no display needed."""

import pytest

from lechery.content.game import new_world
from lechery.world import Area, Direction as D, Room, World


def make_pair():
    area = Area(id="a", name="Area")
    one = area.make_room("one", "One")
    two = area.make_room("two", "Two")
    world = World()
    world.add_area(area)
    return world, one, two


# -- structure ------------------------------------------------------------


def test_area_adopts_rooms_and_sets_first_as_entry():
    area = Area(id="a", name="Area")
    first = area.make_room("first", "First")
    area.make_room("second", "Second")
    assert first.area_id == "a"
    assert area.entry_room is first
    assert len(area) == 2


def test_duplicate_room_id_in_area_is_rejected():
    area = Area(id="a", name="Area")
    area.make_room("dup", "One")
    with pytest.raises(ValueError):
        area.make_room("dup", "Two")


def test_duplicate_room_id_across_areas_is_rejected():
    world = World()
    first = Area(id="a", name="A")
    first.make_room("shared", "One")
    second = Area(id="b", name="B")
    second.make_room("shared", "Two")
    world.add_area(first)
    with pytest.raises(ValueError):
        world.add_area(second)


def test_assembled_game_world_validates():
    assert new_world(seed=1)[0].validate() == []


def test_validate_reports_dangling_exit():
    world, one, _ = make_pair()
    one.link(D.EAST, "nowhere")
    assert any("nowhere" in problem for problem in world.validate())


# -- movement -------------------------------------------------------------


def test_connect_creates_a_two_way_link():
    world, one, two = make_pair()
    one.connect(D.NORTH, two)
    world.place(one)
    assert world.move(D.NORTH).room is two
    assert world.move(D.SOUTH).room is one


def test_move_accepts_a_string_key():
    world, one, two = make_pair()
    one.link("crawl", two)
    world.place(one)
    result = world.move("CRAWL")  # keys normalise case
    assert result.ok and result.room is two


def test_move_into_a_missing_exit_fails_without_moving():
    world, one, _ = make_pair()
    world.place(one)
    result = world.move(D.UP)
    assert not result
    assert world.current_room is one


def test_gate_blocks_passage_and_reports_its_message():
    world, one, two = make_pair()
    one.link(D.NORTH, two, gate=lambda actor: False, blocked_message="It is barred.")
    world.place(one)
    result = world.move(D.NORTH)
    assert not result.ok
    assert result.message == "It is barred."
    assert world.current_room is one


def test_gate_is_consulted_per_move():
    world, one, two = make_pair()
    key = {"held": False}
    one.link(D.NORTH, two, gate=lambda actor: key["held"])
    world.place(one)
    assert not world.move(D.NORTH)
    key["held"] = True
    assert world.move(D.NORTH).room is two


def test_move_to_unregistered_room_raises():
    world, one, _ = make_pair()
    one.link(D.EAST, "ghost")
    world.place(one)
    with pytest.raises(KeyError):
        world.move(D.EAST)


# -- room state -----------------------------------------------------------


def test_hidden_exits_are_traversable_but_unlisted():
    world, one, two = make_pair()
    one.link(D.NORTH, two, hidden=True)
    world.place(one)
    assert one.available_exits() == []
    assert world.move(D.NORTH).room is two


def test_entering_marks_visited_and_fires_hooks_in_order():
    events = []
    world, one, two = make_pair()
    one.connect(D.NORTH, two)
    two.on_enter = lambda room, actor: events.append("enter")
    one.on_exit = lambda room, actor: events.append("exit")
    world.place(one)
    assert not two.visited
    world.move(D.NORTH)
    assert two.visited
    assert events == ["exit", "enter"]


def test_first_enter_hook_runs_once_before_on_enter():
    events = []

    class Once(Room):
        def on_first_enter(self, actor=None):
            events.append("first")

    area = Area(id="a", name="A")
    start = area.make_room("start", "Start")
    once = area.add(Once(id="once", name="Once"))
    once.on_enter = lambda room, actor: events.append("enter")
    start.connect(D.NORTH, once)
    world = World()
    world.add_area(area)
    world.place(start)

    world.move(D.NORTH)
    world.move(D.SOUTH)
    world.move(D.NORTH)
    assert events == ["first", "enter", "enter"]


def test_describe_can_vary_with_state():
    class Shifting(Room):
        def describe(self, actor=None):
            return "lit" if self.flags.get("lamp") else "dark"

    room = Shifting(id="r", name="R")
    assert room.describe() == "dark"
    room.flags["lamp"] = True
    assert room.describe() == "lit"


def test_direction_opposites_are_symmetric():
    for direction in D:
        assert direction.opposite.opposite is direction
