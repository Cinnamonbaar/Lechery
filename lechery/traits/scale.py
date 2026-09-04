"""Numbers that also know what they are called.

Every physical trait is a number a transformation can do arithmetic on, and
a word prose and the paperdoll can read. Without this layer every piece of
content invents its own thresholds, and they drift: one scene calls 150cm
"short" and the next calls it "tiny".

A Scale owns that mapping once.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence


@dataclass(frozen=True)
class Band:
    """One named stretch of a scale. `upper` is exclusive."""

    label: str
    upper: float

    #: Optional adjective for prose that needs one ("a tall woman").
    adjective: str = ""


@dataclass(frozen=True)
class Scale:
    """An ordered set of bands over a numeric range."""

    name: str
    minimum: float
    maximum: float
    bands: Sequence[Band]
    unit: str = ""

    def clamp(self, value: float) -> float:
        return max(self.minimum, min(self.maximum, value))

    def band_for(self, value: float) -> Band:
        """The band a value falls in. The last band catches everything above."""
        for band in self.bands:
            if value < band.upper:
                return band
        return self.bands[-1]

    def label(self, value: float) -> str:
        return self.band_for(value).label

    def adjective(self, value: float) -> str:
        band = self.band_for(value)
        return band.adjective or band.label

    def index(self, value: float) -> int:
        """Which band, as a number. Comparing bands is how content asks
        whether a change was a step up or down without knowing the labels."""
        band = self.band_for(value)
        return list(self.bands).index(band)

    def format(self, value: float) -> str:
        if not self.unit:
            return self.label(value)
        rounded = int(round(value))
        return f"{rounded}{self.unit} ({self.label(value)})"


# -- the scales themselves ------------------------------------------------

#: Adults only. The floor is enforced by the trait model, not just described
#: here, so no code path can produce a character below it.
MINIMUM_AGE = 18

AGE = Scale(
    name="age",
    minimum=MINIMUM_AGE,
    maximum=90,
    unit="",
    bands=(
        Band("young adult", 26),
        Band("adult", 40),
        Band("middle-aged", 60),
        Band("old", 999),
    ),
)

HEIGHT = Scale(
    name="height",
    minimum=120,
    maximum=230,
    unit="cm",
    bands=(
        Band("very short", 150, "diminutive"),
        Band("short", 163),
        Band("average height", 178, "average"),
        Band("tall", 193),
        Band("towering", 999, "immense"),
    ),
)

#: Chest development, as a cup index: 0 is flat, rising from there. Kept as a
#: number rather than a letter so transformations can step it up and down.
BUST = Scale(
    name="bust",
    minimum=0,
    maximum=12,
    bands=(
        Band("flat", 1),
        Band("small", 3),
        Band("modest", 5),
        Band("full", 7),
        Band("large", 9),
        Band("very large", 999),
    ),
)

#: Length in centimetres; zero means absent, which is a real state in a game
#: about bodies changing, not a missing value.
PHALLUS = Scale(
    name="phallus",
    minimum=0,
    maximum=45,
    unit="cm",
    bands=(
        Band("absent", 1),
        Band("small", 12),
        Band("average", 18),
        Band("large", 25),
        Band("very large", 999),
    ),
)

SCALES = {scale.name: scale for scale in (AGE, HEIGHT, BUST, PHALLUS)}


def scale_for(name: str) -> Optional[Scale]:
    return SCALES.get(name)
