"""Exits: the directed edges between rooms."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Optional

from .direction import Direction, as_key

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .room import Room
    from .world import World


#: A gate is any callable that inspects the travelling actor and decides
#: whether passage is allowed. `actor` is deliberately untyped for now --
#: there is no Player class yet, and exits should not be the reason one gets
#: designed prematurely.
Gate = Callable[[object], bool]


@dataclass
class Exit:
    """A one-way connection from one room to another.

    Two-way passages are two `Exit` objects; see `Room.connect`. Keeping them
    one-way means a passage can be asymmetric (you can drop down a shaft but
    not climb back up) without a special case.
    """

    #: Id of the destination room. Stored as an id rather than an object so
    #: content modules can reference rooms that do not exist yet.
    target: str

    #: How the exit is addressed: a Direction, or a free-form verb.
    key: Direction | str = Direction.NORTH

    #: Player-facing label. Defaults to the key's own wording.
    label: Optional[str] = None

    #: Shown instead of travelling when the exit is barred.
    blocked_message: str = "You can't go that way."

    #: Hidden exits are traversable but not listed until discovered.
    hidden: bool = False

    #: Optional predicate; when it returns False the exit is barred.
    gate: Optional[Gate] = field(default=None, repr=False)

    @property
    def key_str(self) -> str:
        return as_key(self.key)

    @property
    def display_label(self) -> str:
        if self.label:
            return self.label
        if isinstance(self.key, Direction):
            return self.key.label
        return self.key.capitalize()

    def is_open(self, actor: object = None) -> bool:
        """Whether `actor` may currently use this exit."""
        return self.gate is None or bool(self.gate(actor))

    def is_visible(self, actor: object = None) -> bool:
        """Whether this exit should be listed in the UI."""
        return not self.hidden

    def destination(self, world: "World") -> "Room":
        return world.room(self.target)
