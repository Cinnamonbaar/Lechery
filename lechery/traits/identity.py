"""Who the character is, as opposed to what body they are in.

These are kept apart deliberately. In a game about bodies changing, tying
gender to a body configuration means every transformation silently rewrites
who the character is -- grow a chest and the game starts calling you "she"
without asking. Identity moves when the story moves it; the body moves when
the body moves.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Pronouns:
    subject: str  # she
    object: str  # her
    possessive: str  # her
    possessive_noun: str  # hers
    reflexive: str  # herself

    #: Whether the pronoun takes a plural verb ("they are" vs "she is").
    plural: bool = False

    def verb(self, singular: str, plural: str) -> str:
        """Pick the verb form this pronoun needs: `p.verb("is", "are")`."""
        return plural if self.plural else singular

    def __str__(self) -> str:
        return f"{self.subject}/{self.object}"


SHE = Pronouns("she", "her", "her", "hers", "herself")
HE = Pronouns("he", "him", "his", "his", "himself")
THEY = Pronouns("they", "them", "their", "theirs", "themselves", plural=True)
IT = Pronouns("it", "it", "its", "its", "itself")

PRONOUN_SETS = {"she": SHE, "he": HE, "they": THEY, "it": IT}


@dataclass
class Gender:
    """A gender identity, with the pronouns that go with it.

    Free-form rather than an enum: this is a label the character carries,
    and the set of them is content, not code. The defaults below are a
    starting list, not a closed one.
    """

    label: str
    pronouns: Pronouns = THEY

    def __str__(self) -> str:
        return self.label


WOMAN = Gender("woman", SHE)
MAN = Gender("man", HE)
NONBINARY = Gender("nonbinary", THEY)

GENDERS = {g.label: g for g in (WOMAN, MAN, NONBINARY)}
