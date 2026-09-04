"""The trait model: what a character is made of, and how it changes.

Every change goes through `set` or `adjust` and comes back as a Change
record. That is the point of the class: a transformation game needs to
narrate what moved and in which direction, and if content had to diff the
body by hand before and after every effect, half of it would forget.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterator, Optional

from .palette import Colour, colour
from .scale import MINIMUM_AGE, Scale, scale_for


@dataclass(frozen=True)
class Change:
    """One trait moving from one value to another."""

    key: str
    before: Any
    after: Any

    #: +1 grew, -1 shrank, 0 changed without an order (a colour).
    direction: int = 0

    #: Whether the change crossed into a different band -- "a bit taller"
    #: versus "tall now". Content usually only wants to narrate the latter.
    crossed_band: bool = False

    @property
    def grew(self) -> bool:
        return self.direction > 0

    @property
    def shrank(self) -> bool:
        return self.direction < 0


@dataclass(frozen=True)
class TraitDef:
    """What a trait is: how to validate it, and how to say it."""

    key: str
    label: str

    #: Numeric traits name a Scale; the rest validate their own way.
    scale: Optional[str] = None

    #: Coerces and validates an incoming value. Raises ValueError if bad.
    coerce: Optional[Callable[[Any], Any]] = None

    def clean(self, value: Any) -> Any:
        if self.coerce is not None:
            return self.coerce(value)
        scale = scale_for(self.scale) if self.scale else None
        if scale is not None:
            return scale.clamp(float(value))
        return value


def _clean_name(value: Any) -> str:
    name = str(value).strip()
    if not name:
        raise ValueError("a character needs a name")
    return name[:40]


def _clean_age(value: Any) -> float:
    age = float(value)
    # Enforced here rather than only clamped, so a caller passing a child's
    # age gets an error instead of a silent correction they never notice.
    if age < MINIMUM_AGE:
        raise ValueError(f"age must be at least {MINIMUM_AGE}")
    return min(age, 90.0)


def _clean_colour(value: Any) -> Colour:
    return value if isinstance(value, Colour) else colour(str(value))


TRAITS: dict[str, TraitDef] = {
    definition.key: definition
    for definition in (
        TraitDef("name", "Name", coerce=_clean_name),
        TraitDef("age", "Age", scale="age", coerce=_clean_age),
        TraitDef("height", "Height", scale="height"),
        TraitDef("hair_colour", "Hair", coerce=_clean_colour),
        TraitDef("eye_colour", "Eyes", coerce=_clean_colour),
        TraitDef("bust", "Bust", scale="bust"),
        TraitDef("phallus", "Phallus", scale="phallus"),
    )
}


class Traits:
    """A character's trait values, and the history of what changed them."""

    def __init__(self, values: Optional[dict[str, Any]] = None) -> None:
        self._values: dict[str, Any] = {}
        self.history: list[Change] = []
        #: Called with each Change. The session hooks this up to the log, so
        #: a transformation narrates itself wherever it is triggered from.
        self.on_change: Optional[Callable[[Change], None]] = None
        for key, value in (values or {}).items():
            self._values[key] = TRAITS[key].clean(value)

    # -- reading ----------------------------------------------------------

    def __contains__(self, key: object) -> bool:
        return key in self._values

    def get(self, key: str, default: Any = None) -> Any:
        return self._values.get(key, default)

    def __getitem__(self, key: str) -> Any:
        try:
            return self._values[key]
        except KeyError:
            raise KeyError(f"Character has no trait {key!r}") from None

    def scale_of(self, key: str) -> Optional[Scale]:
        definition = TRAITS.get(key)
        return scale_for(definition.scale) if definition and definition.scale else None

    def label(self, key: str) -> str:
        """The word for a trait's current value: "tall", "ash blonde"."""
        value = self[key]
        scale = self.scale_of(key)
        return scale.label(value) if scale else str(value)

    def describe(self, key: str) -> str:
        """The value as prose would give it: "172cm (average height)"."""
        value = self[key]
        scale = self.scale_of(key)
        return scale.format(value) if scale else str(value)

    def items(self) -> Iterator[tuple[str, Any]]:
        return iter(self._values.items())

    # -- writing ----------------------------------------------------------

    def set(self, key: str, value: Any) -> Optional[Change]:
        """Set a trait. Returns the Change, or None if nothing moved."""
        if key not in TRAITS:
            raise KeyError(f"Unknown trait {key!r}")

        before = self._values.get(key)
        after = TRAITS[key].clean(value)
        if before == after:
            return None

        scale = self.scale_of(key)
        direction = 0
        crossed = True
        if scale is not None and before is not None:
            direction = (after > before) - (after < before)
            crossed = scale.index(after) != scale.index(before)
        elif before is None:
            crossed = False  # the initial value is not a transformation

        self._values[key] = after
        change = Change(key, before, after, direction, crossed)
        if before is not None:
            self.history.append(change)
            if self.on_change is not None:
                self.on_change(change)
        return change

    def adjust(self, key: str, delta: float) -> Optional[Change]:
        """Move a numeric trait by `delta`. The usual transformation verb."""
        if self.scale_of(key) is None:
            raise TypeError(f"Trait {key!r} is not numeric and cannot be adjusted")
        return self.set(key, float(self[key]) + delta)

    def update(self, values: dict[str, Any]) -> list[Change]:
        return [c for c in (self.set(k, v) for k, v in values.items()) if c is not None]
