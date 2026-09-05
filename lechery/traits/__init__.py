"""Traits: who a character is, and what body they are currently in.

Identity and body are separate on purpose -- see `identity`. Every physical
trait carries a number for transformations to work on and a word for prose
and the paperdoll to read, and every change comes back as an event so it can
narrate itself.
"""

from .character import Character, default_character
from .identity import GENDERS, HE, PRONOUN_SETS, SHE, THEY, Gender, Pronouns
from .palette import EYE_COLOURS, HAIR_COLOURS, Colour, colour
from .perception import CLOTHED, GLIMPSED, NUDE, Read, Visibility, perceive, presentation
from .scale import BUST, HEIGHT, MINIMUM_AGE, PHALLUS, Band, Scale, cup_size, scale_for
from .traits import TRAITS, Change, TraitDef, Traits

__all__ = [
    "BUST",
    "CLOTHED",
    "Band",
    "Change",
    "Character",
    "Colour",
    "EYE_COLOURS",
    "GENDERS",
    "GLIMPSED",
    "Gender",
    "HAIR_COLOURS",
    "HE",
    "HEIGHT",
    "MINIMUM_AGE",
    "NUDE",
    "PHALLUS",
    "PRONOUN_SETS",
    "Pronouns",
    "Read",
    "SHE",
    "Scale",
    "cup_size",
    "THEY",
    "TRAITS",
    "TraitDef",
    "Traits",
    "Visibility",
    "colour",
    "default_character",
    "perceive",
    "presentation",
    "scale_for",
]
