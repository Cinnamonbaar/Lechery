"""A dungeon layout generator: critical path plus branches.

The algorithm is deliberately not a maze. Mazes are hostile to a game where
the player reads prose in every room -- they generate long stretches of
nothing. Instead it carves one guaranteed route from entrance to exit (the
critical path), then hangs short dead-end branches off it for optional
rewards. That gives a shape you can reason about: the player cannot get
lost for long, and every dead end is a promise of something worth finding.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional

from ..world.roles import Role
from .layout import STEPS, Layout, Node, Position


@dataclass
class DungeonShape:
    """Tuning for `generate_dungeon`. All lengths are in rooms."""

    #: Rooms on the guaranteed entrance-to-exit route, inclusive of both.
    critical_path: tuple[int, int] = (6, 9)

    #: How many optional dead-end branches to attempt.
    branches: tuple[int, int] = (2, 4)

    #: Rooms per branch.
    branch_length: tuple[int, int] = (1, 2)

    #: Give the last critical-path room before the exit a BOSS role.
    boss_before_exit: bool = False

    #: Chance that a non-special critical-path room is a COMBAT room.
    combat_density: float = 0.5

    #: Chance a branch dead end holds treasure rather than a fight.
    treasure_chance: float = 0.75


def generate_dungeon(
    shape: DungeonShape | None = None,
    rng: random.Random | None = None,
    *,
    prefix: str = "n",
) -> Layout:
    """Build a dungeon layout. Same rng seed, same layout."""
    shape = shape or DungeonShape()
    rng = rng or random.Random()
    layout = Layout()
    counter = _Counter(prefix)

    path = _carve_critical_path(layout, shape, rng, counter)
    _assign_path_roles(path, shape, rng)
    _carve_branches(layout, path, shape, rng, counter)
    return layout


# -- critical path --------------------------------------------------------


def _carve_critical_path(
    layout: Layout, shape: DungeonShape, rng: random.Random, counter: "_Counter"
) -> list[Node]:
    """A self-avoiding random walk from the entrance."""
    target_length = rng.randint(*shape.critical_path)
    start = layout.add(Node(id=counter.next(), position=(0, 0), role=Role.ENTRANCE))
    path = [start]

    while len(path) < target_length:
        current = path[-1]
        options = _free_neighbours(layout, current.position, rng)
        if not options:
            # Walked into a corner. Back up and try a different turn; if the
            # whole path is boxed in, stop short rather than loop forever.
            if len(path) == 1:
                break
            path.pop()
            continue
        node = layout.add(Node(id=counter.next(), position=options[0]))
        layout.connect(current, node)
        path.append(node)

    return path


def _assign_path_roles(path: list[Node], shape: DungeonShape, rng: random.Random) -> None:
    path[0].role = Role.ENTRANCE
    if len(path) < 2:
        return
    path[-1].role = Role.EXIT

    middle = path[1:-1]
    if shape.boss_before_exit and middle:
        middle[-1].role = Role.BOSS
        middle = middle[:-1]

    for node in middle:
        node.role = Role.COMBAT if rng.random() < shape.combat_density else Role.PASSAGE


# -- branches -------------------------------------------------------------


def _carve_branches(
    layout: Layout,
    path: list[Node],
    shape: DungeonShape,
    rng: random.Random,
    counter: "_Counter",
) -> None:
    """Hang dead-end spurs off the critical path.

    Branch roots are drawn from the middle of the path: branching off the
    entrance makes the first choice meaningless, and off the exit makes the
    reward pointless once you have already finished.
    """
    candidates = path[1:-1] or path
    attempts = rng.randint(*shape.branches)

    for _ in range(attempts):
        root = rng.choice(candidates)
        spur = _carve_spur(layout, root, rng.randint(*shape.branch_length), rng, counter)
        if not spur:
            continue
        tip = spur[-1]
        tip.role = Role.TREASURE if rng.random() < shape.treasure_chance else Role.COMBAT


def _carve_spur(
    layout: Layout,
    root: Node,
    length: int,
    rng: random.Random,
    counter: "_Counter",
) -> list[Node]:
    spur: list[Node] = []
    current = root
    for _ in range(length):
        options = _free_neighbours(layout, current.position, rng)
        if not options:
            break
        node = layout.add(Node(id=counter.next(), position=options[0]))
        layout.connect(current, node)
        spur.append(node)
        current = node
    return spur


# -- helpers --------------------------------------------------------------


def _free_neighbours(layout: Layout, position: Position, rng: random.Random) -> list[Position]:
    """Unoccupied orthogonal neighbours, shuffled.

    Only empty cells are returned, so the walk never creates a loop. Every
    layout this produces is a tree, which is what keeps dead ends meaningful.
    """
    x, y = position
    options = [(x + dx, y + dy) for dx, dy in STEPS if layout.is_free((x + dx, y + dy))]
    rng.shuffle(options)
    return options


class _Counter:
    """Sequential node ids, so a layout's ids are stable for a given seed."""

    def __init__(self, prefix: str) -> None:
        self.prefix = prefix
        self.count = 0

    def next(self) -> str:
        node_id = f"{self.prefix}{self.count}"
        self.count += 1
        return node_id
