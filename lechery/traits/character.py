"""A character: an identity, and a body that can be changed out from under it."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ..stats import Skills, StatBlock
from .identity import GENDERS, THEY, Gender, Pronouns
from .palette import colour
from .perception import CLOTHED, Read, Visibility, perceive, presentation
from .traits import Change, Traits


@dataclass
class Character:
    traits: Traits = field(default_factory=Traits)
    gender: Gender = field(default_factory=lambda: GENDERS["nonbinary"])

    #: Set to override the pronouns the gender would imply. Kept separate so
    #: a character can change gender without losing a chosen pronoun set.
    pronoun_override: Optional[Pronouns] = None

    #: Capability, as opposed to body. A transformation changes traits and
    #: must not silently make you better at arguing; when content wants both
    #: to move it says so.
    stats: StatBlock = field(default_factory=StatBlock)
    skills: Skills = field(default_factory=Skills)

    #: Who they were before they were pulled here.
    backstory_id: Optional[str] = None

    #: How clothing, manner and grooming push the read, from -1 (masculine)
    #: to +1 (feminine). Not a trait: a character can change how they dress
    #: without changing. Content sets it; nothing derives it.
    presentation_bias: float = 0.0

    # -- identity ---------------------------------------------------------

    @property
    def name(self) -> str:
        return self.traits.get("name", "someone")

    @property
    def pronouns(self) -> Pronouns:
        return self.pronoun_override or self.gender.pronouns

    # -- how others see this character -------------------------------------

    def presentation(self, visibility: Visibility = CLOTHED) -> Read:
        """What the body reads as, to someone who does not know them."""
        return presentation(self, visibility)

    def perceived_by(
        self, visibility: Visibility = CLOTHED, *, knows_identity: bool = False
    ) -> Read:
        """What one observer concludes. See `traits.perception`."""
        return perceive(self, visibility, knows_identity=knows_identity)

    @property
    def read_matches_identity(self) -> bool:
        """Whether a stranger would land on the character's own pronouns.

        The state a lot of this game's social content hangs off: false is
        not a bug, it is a situation.
        """
        return self.presentation().pronouns(hedge=False) is self.pronouns

    # -- body -------------------------------------------------------------

    @property
    def has_bust(self) -> bool:
        return float(self.traits.get("bust", 0)) >= 1

    @property
    def has_phallus(self) -> bool:
        """Zero is a real state, not a missing value: bodies change here."""
        return float(self.traits.get("phallus", 0)) >= 1

    def summary(self) -> str:
        """A one-line description, for the character bar and for debugging."""
        traits = self.traits
        parts = [
            f"{int(traits.get('age', 0))}",
            str(self.gender),
            traits.label("height"),
            f"{traits.label('hair_colour')} hair",
            f"{traits.label('eye_colour')} eyes",
        ]
        return f"{self.name} — " + ", ".join(parts)

    # -- convenience ------------------------------------------------------

    def set(self, key: str, value: Any) -> Optional[Change]:
        return self.traits.set(key, value)

    def adjust(self, key: str, delta: float) -> Optional[Change]:
        return self.traits.adjust(key, delta)


def default_character(name: str = "Wanderer") -> Character:
    """The character a new game starts with, until creation exists."""
    return Character(
        traits=Traits(
            {
                "name": name,
                "age": 24,
                "height": 170,
                "hair_colour": colour("dark brown"),
                "eye_colour": colour("hazel"),
                "bust": 0,
                "phallus": 0,
            }
        ),
        gender=GENDERS["nonbinary"],
    )
