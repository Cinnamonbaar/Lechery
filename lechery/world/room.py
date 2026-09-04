"""Rooms: a single place the player can occupy."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Iterator, Optional

from .direction import Direction, as_key
from .exits import Exit, Gate
from .roles import Role

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .world import World


#: Called when the player enters or leaves. Signature is (room, actor).
RoomHook = Callable[["Room", object], None]


@dataclass
class Room:
    """One discrete place.

    Subclass this for rooms that need behaviour (a shop, a trap, an encounter
    node). The base class deliberately knows nothing about combat, items or
    the player -- it is geography and description only.
    """

    id: str
    name: str

    #: Long-form prose shown on entry. Overridable via `describe()`.
    description: str = ""

    #: Id of the owning Area, set by `Area.add`.
    area_id: Optional[str] = None

    #: What this room is for. Set by the generator, or by hand.
    role: Role = Role.PASSAGE

    #: Grid position within its area, when it has one. Used by layout
    #: generation and by any future map screen; None for rooms placed by
    #: hand without a coordinate.
    position: Optional[tuple[int, int]] = None

    #: Free-form markers content can query: "indoors", "safe", "water".
    tags: set[str] = field(default_factory=set)

    #: Per-room mutable state (switch thrown, chest looted, npc met).
    flags: dict[str, object] = field(default_factory=dict)

    #: Exits keyed by their normalised key string.
    exits: dict[str, Exit] = field(default_factory=dict, repr=False)

    #: True once the player has entered at least once.
    visited: bool = False

    on_enter: Optional[RoomHook] = field(default=None, repr=False)
    on_exit: Optional[RoomHook] = field(default=None, repr=False)

    # -- description ------------------------------------------------------

    def describe(self, actor: object = None) -> str:
        """The prose for this room.

        Overridden by subclasses that vary their text by world state; the
        base implementation is just the static `description`.
        """
        return self.description

    # -- exits ------------------------------------------------------------

    def add_exit(self, exit_: Exit) -> Exit:
        """Register an exit, replacing any existing one on the same key."""
        self.exits[exit_.key_str] = exit_
        return exit_

    def link(
        self,
        direction: Direction | str,
        target: "str | Room",
        *,
        label: Optional[str] = None,
        hidden: bool = False,
        gate: Optional[Gate] = None,
        blocked_message: str = "You can't go that way.",
    ) -> Exit:
        """Create a one-way exit from this room."""
        target_id = target if isinstance(target, str) else target.id
        return self.add_exit(
            Exit(
                target=target_id,
                key=direction,
                label=label,
                hidden=hidden,
                gate=gate,
                blocked_message=blocked_message,
            )
        )

    def connect(
        self,
        direction: Direction,
        other: "Room",
        *,
        back: Optional[Direction] = None,
        **kwargs,
    ) -> tuple[Exit, Exit]:
        """Link two rooms both ways.

        The return exit uses `direction.opposite` unless `back` overrides it.
        Only compass-style directions can be auto-reversed, which is why this
        takes a `Direction` rather than a free-form key.
        """
        forward = self.link(direction, other, **kwargs)
        backward = other.link(back or direction.opposite, self, **kwargs)
        return forward, backward

    def exit_for(self, key: Direction | str) -> Optional[Exit]:
        return self.exits.get(as_key(key))

    def available_exits(self, actor: object = None) -> list[Exit]:
        """Exits the UI should offer: visible, in insertion order."""
        return [e for e in self.exits.values() if e.is_visible(actor)]

    def neighbours(self, world: "World") -> Iterator["Room"]:
        for exit_ in self.exits.values():
            yield exit_.destination(world)

    # -- lifecycle --------------------------------------------------------

    def enter(self, actor: object = None) -> None:
        """Called by the World after the player has been moved in."""
        first_visit = not self.visited
        self.visited = True
        if first_visit:
            self.on_first_enter(actor)
        if self.on_enter is not None:
            self.on_enter(self, actor)

    def on_first_enter(self, actor: object = None) -> None:
        """Hook for subclasses; runs once, before `on_enter`."""

    def leave(self, actor: object = None) -> None:
        if self.on_exit is not None:
            self.on_exit(self, actor)

    # -- tags -------------------------------------------------------------

    def has_tag(self, tag: str) -> bool:
        return tag in self.tags

    def tag(self, *tags: str) -> "Room":
        self.tags.update(tags)
        return self

    def __str__(self) -> str:
        return self.name
