"""Room templates: the content a layout node gets dressed in.

A template is a recipe for a Room, not a Room. One template can produce many
rooms across many playthroughs, so it must not hold per-playthrough state --
`build()` returns a fresh Room every time.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable, Optional, Sequence

from ..world.roles import Role
from ..world.room import Room

#: Lets a template produce a Room subclass (a shop, a trap, a scripted scene)
#: instead of a plain Room. Receives the room id and the chosen description.
RoomFactory = Callable[[str, str], Room]


@dataclass
class RoomTemplate:
    """A recipe for one kind of room."""

    id: str
    name: str

    #: Description variants. One is chosen per room, so the same template
    #: used twice in a dungeon does not read as copy-paste.
    descriptions: Sequence[str] = ()

    #: Roles this template may fill. Empty means "any role".
    roles: frozenset[Role] = frozenset()

    #: Relative likelihood against other eligible templates.
    weight: float = 1.0

    #: A template with `unique` set appears at most once per area.
    unique: bool = False

    tags: frozenset[str] = frozenset()

    #: Builds a Room subclass when a plain Room will not do.
    factory: Optional[RoomFactory] = field(default=None, repr=False)

    def accepts(self, role: Role) -> bool:
        return not self.roles or role in self.roles

    def build(self, room_id: str, role: Role, rng: random.Random) -> Room:
        description = rng.choice(list(self.descriptions)) if self.descriptions else ""
        room = self.factory(room_id, description) if self.factory else Room(
            id=room_id, name=self.name, description=description
        )
        room.role = role
        room.tags.update(self.tags)
        room.flags.setdefault("template", self.id)
        return room


class TemplatePool:
    """The set of templates available to one area.

    Selection is weighted-random among templates eligible for the node's
    role, minus any already-used unique ones. Templates recently used are
    down-weighted so a corridor of six identical rooms is unlikely without
    being forbidden.
    """

    #: Multiplier applied to a template used within the last few picks.
    REPEAT_PENALTY = 0.25

    #: How many recent picks the penalty remembers.
    MEMORY = 3

    def __init__(self, templates: Sequence[RoomTemplate] = ()) -> None:
        self.templates: dict[str, RoomTemplate] = {}
        for template in templates:
            self.add(template)
        self._used_unique: set[str] = set()
        self._recent: list[str] = []

    def add(self, template: RoomTemplate) -> RoomTemplate:
        if template.id in self.templates:
            raise ValueError(f"Duplicate template id {template.id!r}")
        self.templates[template.id] = template
        return template

    def get(self, template_id: str) -> RoomTemplate:
        try:
            return self.templates[template_id]
        except KeyError:
            raise KeyError(f"No template {template_id!r} in pool") from None

    def eligible(self, role: Role) -> list[RoomTemplate]:
        return [
            t
            for t in self.templates.values()
            if t.accepts(role) and not (t.unique and t.id in self._used_unique)
        ]

    def pick(self, role: Role, rng: random.Random) -> RoomTemplate:
        candidates = self.eligible(role)
        if not candidates:
            raise LookupError(f"No template in pool can fill role {role}")
        weights = [
            t.weight * (self.REPEAT_PENALTY if t.id in self._recent else 1.0)
            for t in candidates
        ]
        chosen = rng.choices(candidates, weights=weights, k=1)[0]
        self._mark(chosen)
        return chosen

    def _mark(self, template: RoomTemplate) -> None:
        if template.unique:
            self._used_unique.add(template.id)
        self._recent.append(template.id)
        del self._recent[: -self.MEMORY]

    def reset(self) -> None:
        """Forget usage history, so the pool can build another area."""
        self._used_unique.clear()
        self._recent.clear()
