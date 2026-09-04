"""Tests for layout generation, templates, and world assembly."""

import random

import pytest

from lechery.content.areas import plains, tutorial
from lechery.content.game import new_game
from lechery.generation import (
    DungeonShape,
    Layout,
    Node,
    RoomTemplate,
    TemplatePool,
    build_area,
    derive_seed,
    generate_dungeon,
    rng_for,
)
from lechery.world import Role

SEEDS = list(range(40))


# -- layout ---------------------------------------------------------------


def test_layout_rejects_two_nodes_in_one_cell():
    layout = Layout()
    layout.add(Node(id="a", position=(0, 0)))
    with pytest.raises(ValueError):
        layout.add(Node(id="b", position=(0, 0)))


def test_layout_validate_rejects_non_adjacent_link():
    layout = Layout()
    layout.add(Node(id="a", position=(0, 0)))
    layout.add(Node(id="b", position=(5, 5)))
    layout.connect("a", "b")
    assert any("not adjacent" in p for p in layout.validate())


def test_layout_validate_rejects_disconnected_graph():
    layout = Layout()
    layout.add(Node(id="a", position=(0, 0)))
    layout.add(Node(id="b", position=(1, 0)))
    assert any("not fully connected" in p for p in layout.validate())


# -- the dungeon generator ------------------------------------------------


@pytest.mark.parametrize("seed", SEEDS)
def test_generated_dungeons_are_always_valid(seed):
    layout = generate_dungeon(rng=random.Random(seed))
    assert layout.validate() == []


@pytest.mark.parametrize("seed", SEEDS)
def test_every_dungeon_has_exactly_one_entrance_and_one_exit(seed):
    layout = generate_dungeon(rng=random.Random(seed))
    assert len(layout.with_role(Role.ENTRANCE)) == 1
    assert len(layout.with_role(Role.EXIT)) == 1


@pytest.mark.parametrize("seed", SEEDS)
def test_the_exit_is_always_reachable_from_the_entrance(seed):
    """The property the whole generator exists to guarantee."""
    layout = generate_dungeon(rng=random.Random(seed))
    entrance = layout.with_role(Role.ENTRANCE)[0]
    exit_node = layout.with_role(Role.EXIT)[0]

    seen = {entrance.id}
    frontier = [entrance]
    while frontier:
        for neighbour in layout.neighbours(frontier.pop()):
            if neighbour.id not in seen:
                seen.add(neighbour.id)
                frontier.append(neighbour)
    assert exit_node.id in seen


def test_generation_is_deterministic_for_a_seed():
    first = generate_dungeon(rng=random.Random(99))
    second = generate_dungeon(rng=random.Random(99))
    assert {n.id: (n.position, n.role) for n in first} == {
        n.id: (n.position, n.role) for n in second
    }


def test_different_seeds_give_different_layouts():
    shapes = {
        tuple(sorted((n.position, n.role.value) for n in generate_dungeon(rng=random.Random(s))))
        for s in range(12)
    }
    assert len(shapes) > 1


def test_boss_room_sits_on_the_critical_path_before_the_exit():
    shape = DungeonShape(boss_before_exit=True)
    layout = generate_dungeon(shape, random.Random(7))
    boss = layout.with_role(Role.BOSS)[0]
    exit_node = layout.with_role(Role.EXIT)[0]
    assert exit_node.id in boss.links


def test_shape_controls_room_count():
    small = generate_dungeon(DungeonShape(critical_path=(3, 3), branches=(0, 0)), random.Random(1))
    assert len(small) == 3


# -- templates ------------------------------------------------------------


def test_pool_only_offers_templates_that_accept_the_role():
    pool = TemplatePool(
        [
            RoomTemplate(id="fight", name="Fight", roles=frozenset({Role.COMBAT})),
            RoomTemplate(id="loot", name="Loot", roles=frozenset({Role.TREASURE})),
        ]
    )
    assert pool.pick(Role.COMBAT, random.Random(0)).id == "fight"
    assert [t.id for t in pool.eligible(Role.TREASURE)] == ["loot"]


def test_pool_raises_when_no_template_fits_a_role():
    pool = TemplatePool([RoomTemplate(id="only", name="Only", roles=frozenset({Role.COMBAT}))])
    with pytest.raises(LookupError):
        pool.pick(Role.BOSS, random.Random(0))


def test_unique_templates_are_offered_only_once():
    pool = TemplatePool(
        [
            RoomTemplate(id="once", name="Once", unique=True),
            RoomTemplate(id="always", name="Always"),
        ]
    )
    rng = random.Random(0)
    picked = {pool.pick(Role.PASSAGE, rng).id for _ in range(8)}
    assert picked == {"once", "always"}
    assert [t.id for t in pool.eligible(Role.PASSAGE)] == ["always"]


def test_reset_makes_unique_templates_available_again():
    pool = TemplatePool([RoomTemplate(id="once", name="Once", unique=True)])
    pool.pick(Role.PASSAGE, random.Random(0))
    pool.reset()
    assert pool.eligible(Role.PASSAGE)


def test_template_builds_a_fresh_room_each_time():
    template = RoomTemplate(id="t", name="T", descriptions=("a",), tags=frozenset({"x"}))
    rng = random.Random(0)
    first = template.build("r1", Role.COMBAT, rng)
    second = template.build("r2", Role.COMBAT, rng)
    first.flags["touched"] = True
    first.tags.add("mutated")
    assert "touched" not in second.flags
    assert "mutated" not in second.tags
    assert second.role is Role.COMBAT


# -- builder --------------------------------------------------------------


def test_builder_wires_exits_in_the_right_directions():
    layout = Layout()
    layout.add(Node(id="a", position=(0, 0), role=Role.ENTRANCE))
    layout.add(Node(id="b", position=(0, -1)))
    layout.connect("a", "b")
    pool = TemplatePool([RoomTemplate(id="any", name="Any")])
    area = build_area(layout, pool, area_id="z", name="Z", rng=random.Random(0))

    north = area.room("z:a").exit_for("north")
    assert north is not None and north.target == "z:b"
    assert area.room("z:b").exit_for("south").target == "z:a"


def test_builder_namespaces_room_ids_by_area():
    layout = Layout()
    layout.add(Node(id="a", position=(0, 0)))
    pool = TemplatePool([RoomTemplate(id="any", name="Any")])
    area = build_area(layout, pool, area_id="cave", name="Cave", rng=random.Random(0))
    assert "cave:a" in area.rooms


def test_pinned_template_overrides_random_choice():
    layout = Layout()
    layout.add(Node(id="a", position=(0, 0), template_id="pinned"))
    pool = TemplatePool(
        [
            RoomTemplate(id="pinned", name="Pinned"),
            RoomTemplate(id="filler", name="Filler", weight=1000.0),
        ]
    )
    area = build_area(layout, pool, area_id="z", name="Z", rng=random.Random(0))
    assert area.room("z:a").name == "Pinned"


# -- seeding --------------------------------------------------------------


def test_derived_seeds_are_stable_and_distinct():
    assert derive_seed(5, "a") == derive_seed(5, "a")
    assert derive_seed(5, "a") != derive_seed(5, "b")
    assert derive_seed(5, "a") != derive_seed(6, "a")


def test_areas_are_independent_of_generation_order():
    """Regenerating one area must not disturb another."""
    first = [n.position for n in generate_dungeon(rng=rng_for(42, "tutorial"))]
    rng_for(42, "caves")  # a whole other area generated in between
    second = [n.position for n in generate_dungeon(rng=rng_for(42, "tutorial"))]
    assert first == second


# -- the assembled world --------------------------------------------------


@pytest.mark.parametrize("seed", range(15))
def test_new_game_builds_a_valid_world(seed):
    world = new_game(seed)
    assert world.validate() == []
    assert world.current_room.role is Role.ENTRANCE


@pytest.mark.parametrize("seed", range(15))
def test_the_town_is_reachable_from_the_starting_room(seed):
    """End to end: spawn, cross the dungeon, reach the hub's haven."""
    world = new_game(seed)
    start = world.current_room

    seen = {start.id}
    frontier = [start]
    while frontier:
        for room in frontier.pop().neighbours(world):
            if room.id not in seen:
                seen.add(room.id)
                frontier.append(room)

    town = world.area(plains.AREA_ID).first_with_role(Role.HAVEN)
    assert town.id in seen


def test_the_dungeon_exit_leads_into_the_plains():
    world = new_game(3)
    dungeon_exit = world.area(tutorial.AREA_ID).first_with_role(Role.EXIT)
    world.place(dungeon_exit)
    result = world.move("up")
    assert result.ok
    assert world.area_of(result.room).id == plains.AREA_ID


def test_the_same_seed_rebuilds_the_same_world():
    first = new_game(77)
    second = new_game(77)
    assert [r.id for r in first.rooms] == [r.id for r in second.rooms]
    assert [r.name for r in first.rooms] == [r.name for r in second.rooms]
