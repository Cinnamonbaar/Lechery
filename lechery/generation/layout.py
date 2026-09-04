"""Layouts: the abstract shape of an area, before it has any content.

A Layout is a graph of nodes on a grid. It knows how many rooms there are,
how they connect, and what each one is *for* -- and nothing about prose,
enemies or items. Keeping the shape separate from the content is what lets
one generator serve every area in the game: the tutorial dungeon and a late
cave can share an algorithm and share nothing else.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, Optional

from ..world.direction import Direction
from ..world.roles import Role

#: Grid coordinate. +x is east, +y is south.
Position = tuple[int, int]

#: Which Direction you travel to go from a position to an adjacent one.
STEPS: dict[Position, Direction] = {
    (0, -1): Direction.NORTH,
    (0, 1): Direction.SOUTH,
    (1, 0): Direction.EAST,
    (-1, 0): Direction.WEST,
}


def direction_between(origin: Position, target: Position) -> Optional[Direction]:
    """The compass direction from `origin` to an orthogonally adjacent cell."""
    return STEPS.get((target[0] - origin[0], target[1] - origin[1]))


@dataclass
class Node:
    """One room-to-be."""

    id: str
    position: Position
    role: Role = Role.PASSAGE

    #: Ids of adjacent nodes. Edges are stored on both nodes.
    links: set[str] = field(default_factory=set)

    #: Pins this node to a specific room template, bypassing random choice.
    #: This is how a handcrafted room lives inside a generated layout.
    template_id: Optional[str] = None

    #: Generator-specific extras the builder may consult.
    data: dict[str, object] = field(default_factory=dict)

    @property
    def degree(self) -> int:
        return len(self.links)

    @property
    def is_dead_end(self) -> bool:
        return self.degree <= 1


class Layout:
    """A graph of nodes, addressable by id or by grid position."""

    def __init__(self) -> None:
        self.nodes: dict[str, Node] = {}
        self._by_position: dict[Position, str] = {}

    # -- building ---------------------------------------------------------

    def add(self, node: Node) -> Node:
        if node.id in self.nodes:
            raise ValueError(f"Duplicate node id {node.id!r}")
        if node.position in self._by_position:
            raise ValueError(f"Two nodes occupy {node.position}")
        self.nodes[node.id] = node
        self._by_position[node.position] = node.id
        return node

    def connect(self, a: "str | Node", b: "str | Node") -> None:
        """Link two nodes both ways."""
        first = self.node(a) if isinstance(a, str) else a
        second = self.node(b) if isinstance(b, str) else b
        if first is second:
            raise ValueError(f"Node {first.id!r} cannot link to itself")
        first.links.add(second.id)
        second.links.add(first.id)

    # -- lookup -----------------------------------------------------------

    def node(self, node_id: str) -> Node:
        try:
            return self.nodes[node_id]
        except KeyError:
            raise KeyError(f"No node {node_id!r} in layout") from None

    def at(self, position: Position) -> Optional[Node]:
        node_id = self._by_position.get(position)
        return self.nodes[node_id] if node_id else None

    def is_free(self, position: Position) -> bool:
        return position not in self._by_position

    def neighbours(self, node: Node) -> Iterator[Node]:
        for node_id in node.links:
            yield self.nodes[node_id]

    def with_role(self, role: Role) -> list[Node]:
        return [n for n in self.nodes.values() if n.role is role]

    def dead_ends(self) -> list[Node]:
        return [n for n in self.nodes.values() if n.is_dead_end]

    @property
    def bounds(self) -> tuple[int, int, int, int]:
        """(min_x, min_y, max_x, max_y) of occupied cells."""
        xs = [p[0] for p in self._by_position]
        ys = [p[1] for p in self._by_position]
        return (min(xs), min(ys), max(xs), max(ys)) if xs else (0, 0, 0, 0)

    def __len__(self) -> int:
        return len(self.nodes)

    def __iter__(self) -> Iterator[Node]:
        return iter(self.nodes.values())

    # -- integrity --------------------------------------------------------

    def is_connected(self) -> bool:
        """Whether every node is reachable from any other.

        A generator that produces an unreachable room has produced a bug the
        player will find eventually; this makes it a test failure instead.
        """
        if not self.nodes:
            return True
        start = next(iter(self.nodes))
        seen = {start}
        frontier = [start]
        while frontier:
            current = self.nodes[frontier.pop()]
            for neighbour in current.links:
                if neighbour not in seen:
                    seen.add(neighbour)
                    frontier.append(neighbour)
        return len(seen) == len(self.nodes)

    def validate(self) -> list[str]:
        problems: list[str] = []
        for node in self.nodes.values():
            for other_id in node.links:
                if other_id not in self.nodes:
                    problems.append(f"{node.id}: links to unknown node {other_id!r}")
                    continue
                if node.id not in self.nodes[other_id].links:
                    problems.append(f"{node.id} -> {other_id}: link is not mutual")
                if direction_between(node.position, self.nodes[other_id].position) is None:
                    problems.append(
                        f"{node.id} -> {other_id}: linked nodes are not adjacent"
                    )
        if not self.is_connected():
            problems.append("layout is not fully connected")
        return problems
