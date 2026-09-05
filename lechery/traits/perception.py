"""How a body reads to someone looking at it.

This is a third axis, distinct from both identity and the body itself:

  identity      what the character is. Only the player changes it.
  presentation  what the body reads as. Derived; nobody sets it directly.
  perception    what one observer concludes, given what they can see and
                whether they already know you.

They are allowed to disagree, and the disagreement is the point -- a game
about bodies changing under you is partly a game about being read wrongly.
Deriving identity from the body would erase that; so would deriving nothing
and having strangers politely use whatever pronouns you picked.

Two rules the model enforces rather than leaves to content:

  A signal only counts if the observer can see it. A stranger across a
  market is not reading anything under your clothes, so parts covered by
  clothing contribute nothing to presentation while dressed. Getting this
  wrong is not a balance problem, it is a modelling bug.

  Knowing someone beats looking at them. An observer who knows the
  character's identity uses it, however the body reads.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from .identity import HE, SHE, THEY, Pronouns
from .scale import BUST, HEIGHT, PHALLUS

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .character import Character


@dataclass(frozen=True)
class Visibility:
    """What an observer can actually make out.

    The default is the common case: a clothed body seen at conversational
    distance. Scenes that undress the character, or put them in a crowd at
    dusk, pass something else.
    """

    #: Whether the body is uncovered. Gates the signals clothing hides.
    nude: bool = False

    #: Scales every signal: a glimpse in poor light reads less than a
    #: face-to-face conversation. 0 means the observer sees nothing useful.
    clarity: float = 1.0

    @property
    def covered(self) -> bool:
        return not self.nude


CLOTHED = Visibility()
NUDE = Visibility(nude=True)
GLIMPSED = Visibility(clarity=0.45)


@dataclass(frozen=True)
class Signal:
    """One readable cue, and how strongly it pushes.

    `weight` is signed: negative reads masculine, positive feminine. The
    numbers are deliberately blunt -- this is a legibility model, not a
    claim about bodies, and every one of them is meant to be tuned by feel
    once there is content to feel it against.
    """

    key: str
    strength: float
    visible: bool = True


#: Where the bands sit on the -1..+1 axis.
AMBIGUOUS_BELOW = 0.34


@dataclass(frozen=True)
class Read:
    """What one observer concluded."""

    score: float
    signals: tuple[Signal, ...] = ()

    #: Set when the observer knows the character and used their identity
    #: rather than reading the body at all.
    from_knowledge: bool = False

    @property
    def ambiguous(self) -> bool:
        return abs(self.score) < AMBIGUOUS_BELOW

    @property
    def label(self) -> str:
        if self.ambiguous:
            return "androgynous"
        return "feminine" if self.score > 0 else "masculine"

    @property
    def confidence(self) -> float:
        """0 at perfectly ambiguous, 1 at unmistakable."""
        return min(1.0, abs(self.score))

    def pronouns(self, hedge: bool = True) -> Pronouns:
        """The pronouns this read implies.

        `hedge` decides what an unsure observer does. A narrator hedges;
        most people guess, and guessing wrong is the interesting outcome,
        so NPCs should usually pass hedge=False.
        """
        if self.ambiguous:
            if hedge:
                return THEY
            return SHE if self.score >= 0 else HE
        return SHE if self.score > 0 else HE


def presentation(character: "Character", visibility: Visibility = CLOTHED) -> Read:
    """How `character` reads to an observer with this much to go on."""
    signals = _signals(character, visibility)
    visible = [s for s in signals if s.visible]
    score = sum(s.strength for s in visible)

    # Style, clothing and manner push the read without being body traits.
    # Content sets this; there is no trait behind it on purpose, because a
    # character can change how they dress without changing.
    score += character.presentation_bias

    score = max(-1.0, min(1.0, score)) * visibility.clarity
    return Read(score=score, signals=tuple(signals))


def perceive(
    character: "Character",
    visibility: Visibility = CLOTHED,
    *,
    knows_identity: bool = False,
) -> Read:
    """What one observer concludes about `character`.

    An observer who knows them uses their identity, however they read --
    that is the whole difference between a stranger and someone who has
    been told, and it is what makes being known worth something.
    """
    if knows_identity:
        return Read(score=_identity_score(character), from_knowledge=True)
    return presentation(character, visibility)


def _signals(character: "Character", visibility: Visibility) -> list[Signal]:
    traits = character.traits

    bust = float(traits.get("bust", 0))
    phallus = float(traits.get("phallus", 0))
    height = float(traits.get("height", 170))

    # Chest reads through clothing -- less plainly than bare, but a shape is
    # a shape. Scaled across the bands rather than a threshold, so growing
    # changes how you are read gradually.
    bust_strength = 0.16 * BUST.index(bust)
    if visibility.covered:
        bust_strength *= 0.8

    # Genitals are a strong signal and almost never a visible one. Gating
    # this is the single most important line in the module.
    phallus_strength = -0.55 if phallus >= 1 else 0.0

    # Height is a weak, unreliable cue, which is exactly how it should
    # behave: it nudges an ambiguous read and never decides one.
    midpoint = 172.0
    height_strength = max(-0.18, min(0.18, (midpoint - height) / 120.0))

    return [
        Signal("bust", bust_strength),
        Signal("phallus", phallus_strength, visible=visibility.nude),
        Signal("height", height_strength),
    ]


def _identity_score(character: "Character") -> float:
    """A score standing in for a known identity, so Read behaves uniformly."""
    pronouns = character.pronouns
    if pronouns is SHE:
        return 1.0
    if pronouns is HE:
        return -1.0
    return 0.0
