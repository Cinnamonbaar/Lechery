"""Turning trait changes into sentences.

Generic by design: this is the fallback so that *any* transformation reads
as something rather than nothing. Scenes that want a specific line should
write one and log it themselves -- content beats a template every time, and
a template that tries to cover every case ends up covering none of them
well.

Changes that stay inside a band are narrated more quietly than ones that
cross out of it, because "you are a little taller" and "you are tall now"
are different events.
"""

from __future__ import annotations

from typing import Optional

from .traits import Character
from .traits.traits import Change

#: Verb pairs per trait: (grew, shrank).
VERBS = {
    "height": ("You stand a little taller.", "You feel yourself shrink."),
    "bust": ("Your chest feels heavier.", "Your chest feels lighter."),
    "phallus": ("There is more of you than there was.", "There is less of you than there was."),
    "age": ("The years settle heavier on you.", "The years lift from you."),
}

#: Sentences for a change that crosses into a new band, where the label is
#: worth stating outright.
CROSSINGS = {
    "height": "You are {label} now.",
    "bust": "Your chest has become {label}.",
    "age": "You have become {label}.",
}


def describe_change(change: Change, character: Character) -> Optional[str]:
    """A line for a trait change, or None if it does not deserve one."""
    if change.key == "name":
        return f"You are called {change.after} now."

    if change.key in ("hair_colour", "eye_colour"):
        part = "hair" if change.key == "hair_colour" else "eyes"
        return f"Your {part} are now {change.after}." if part == "eyes" else (
            f"Your hair is now {change.after}."
        )

    if change.key == "phallus" and _appeared(change):
        return "Something that was not there before is."
    if change.key == "phallus" and _vanished(change):
        return "What was there is not, any more."

    if change.crossed_band and change.key in CROSSINGS:
        label = character.traits.label(change.key)
        return CROSSINGS[change.key].format(label=label)

    verbs = VERBS.get(change.key)
    if verbs is None:
        return None
    return verbs[0] if change.grew else verbs[1]


def _appeared(change: Change) -> bool:
    return float(change.before or 0) < 1 <= float(change.after or 0)


def _vanished(change: Change) -> bool:
    return float(change.before or 0) >= 1 > float(change.after or 0)


#: How it lands when the way strangers read you shifts. Phrased from the
#: character's side rather than an observer's: nobody is in the room when a
#: transformation happens, so what changes in the moment is what you expect
#: to happen next time someone looks.
READ_SHIFTS = {
    ("androgynous", "feminine"): "You would be taken for a woman now, by anyone not looking twice.",
    ("androgynous", "masculine"): "You would be taken for a man now, by anyone not looking twice.",
    ("feminine", "androgynous"): "It is no longer obvious, at a glance, what you are.",
    ("masculine", "androgynous"): "It is no longer obvious, at a glance, what you are.",
    ("feminine", "masculine"): "Strangers would see a man where they used to see a woman.",
    ("masculine", "feminine"): "Strangers would see a woman where they used to see a man.",
}


def describe_read_shift(before: str, after: str, character: Character) -> Optional[str]:
    """A line for the way the character is read having changed.

    Returned separately from the trait change that caused it: growing a
    chest and being read differently because of it are two events, and the
    second is the one this game is actually about.
    """
    line = READ_SHIFTS.get((before, after))
    if line is None:
        return None
    if not character.read_matches_identity:
        # Worth saying outright when the mismatch is the new state, since
        # it is the thing the player will be living with.
        return f"{line} It is not what you are."
    return line
