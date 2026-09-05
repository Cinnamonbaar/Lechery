"""Stats and skills: what a character can do, as opposed to what they are.

Kept apart from traits deliberately. Traits are the body and who lives in
it; these are capability. A transformation changes traits and should not
silently make you better at arguing -- when a change should touch both, the
content says so explicitly.

Stats are few and broad; skills are many and narrow. That split is what
keeps a skill list growable without every new skill needing a stat to hang
off, and what keeps stat checks meaningful when there are eighty skills.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterator, Optional


class Stat(Enum):
    """The five broad capabilities. Checked when no skill fits."""

    VIGOUR = "vigour"      # bodily strength and endurance
    GRACE = "grace"        # speed, balance, dexterity
    WITS = "wits"          # reasoning, memory, quickness of thought
    PRESENCE = "presence"  # charisma, bearing, how much room you take up
    RESOLVE = "resolve"    # will, composure, the ability to keep going

    @property
    def label(self) -> str:
        return self.value.capitalize()


#: Where an ordinary person sits, and the range a character can occupy.
STAT_DEFAULT = 3
STAT_MIN = 1
STAT_MAX = 10

#: Points a player distributes during creation, on top of the default.
CREATION_POINTS = 4

STAT_BANDS = (
    (2, "poor"),
    (4, "ordinary"),
    (6, "capable"),
    (8, "exceptional"),
    (99, "peerless"),
)


def stat_label(value: int) -> str:
    for upper, label in STAT_BANDS:
        if value <= upper:
            return label
    return STAT_BANDS[-1][1]


@dataclass
class StatBlock:
    """A character's five stats."""

    values: dict[Stat, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for stat in Stat:
            self.values.setdefault(stat, STAT_DEFAULT)

    def __getitem__(self, stat: Stat) -> int:
        return self.values[stat]

    def get(self, stat: Stat) -> int:
        return self.values[stat]

    def set(self, stat: Stat, value: int) -> int:
        self.values[stat] = max(STAT_MIN, min(STAT_MAX, int(value)))
        return self.values[stat]

    def adjust(self, stat: Stat, delta: int) -> int:
        return self.set(stat, self.values[stat] + delta)

    def label(self, stat: Stat) -> str:
        return stat_label(self.values[stat])

    @property
    def spent(self) -> int:
        """Points above the baseline, for creation to budget against."""
        return sum(v - STAT_DEFAULT for v in self.values.values())

    def copy(self) -> "StatBlock":
        return StatBlock(values=dict(self.values))

    def items(self) -> Iterator[tuple[Stat, int]]:
        return iter(self.values.items())


@dataclass(frozen=True)
class SkillDef:
    """A named, narrow competence."""

    key: str
    label: str
    stat: Stat
    description: str = ""


#: The starting list. Narrow on purpose -- skills are cheap to add and
#: expensive to remove once content checks them by name.
SKILLS: dict[str, SkillDef] = {
    definition.key: definition
    for definition in (
        SkillDef("athletics", "Athletics", Stat.VIGOUR, "Running, climbing, hauling."),
        SkillDef("brawling", "Brawling", Stat.VIGOUR, "Violence without a plan."),
        SkillDef("fencing", "Fencing", Stat.GRACE, "Violence with one."),
        SkillDef("stealth", "Stealth", Stat.GRACE, "Not being where attention is."),
        SkillDef("sleight", "Sleight", Stat.GRACE, "Hands doing what they should not."),
        SkillDef("lore", "Lore", Stat.WITS, "What is written down, and where."),
        SkillDef("arcana", "Arcana", Stat.WITS, "The rules under the rules."),
        SkillDef("medicine", "Medicine", Stat.WITS, "Keeping a body working."),
        SkillDef("craft", "Craft", Stat.WITS, "Making and mending."),
        SkillDef("survival", "Survival", Stat.WITS, "Weather, tracks, water, dark."),
        SkillDef("persuasion", "Persuasion", Stat.PRESENCE, "Being agreed with."),
        SkillDef("insight", "Insight", Stat.PRESENCE, "Reading what is not said."),
        SkillDef("performance", "Performance", Stat.PRESENCE, "Being watched on purpose."),
        SkillDef("composure", "Composure", Stat.RESOLVE, "Not showing it."),
        SkillDef("endurance", "Endurance", Stat.RESOLVE, "Outlasting the problem."),
    )
}

SKILL_MAX = 5

SKILL_RANKS = ("untrained", "novice", "competent", "practised", "expert", "masterful")


def skill_label(rank: int) -> str:
    return SKILL_RANKS[max(0, min(SKILL_MAX, rank))]


@dataclass
class Skills:
    """Skill ranks, defaulting to untrained.

    Stored sparsely: a character has a rank in a skill or they do not, and
    an absent skill is untrained rather than missing. That keeps the list
    growable without every save file needing every skill written into it.
    """

    ranks: dict[str, int] = field(default_factory=dict)

    def __getitem__(self, key: str) -> int:
        return self.get(key)

    def get(self, key: str) -> int:
        if key not in SKILLS:
            raise KeyError(f"Unknown skill {key!r}")
        return self.ranks.get(key, 0)

    def set(self, key: str, rank: int) -> int:
        if key not in SKILLS:
            raise KeyError(f"Unknown skill {key!r}")
        rank = max(0, min(SKILL_MAX, int(rank)))
        if rank:
            self.ranks[key] = rank
        else:
            self.ranks.pop(key, None)
        return rank

    def adjust(self, key: str, delta: int) -> int:
        return self.set(key, self.get(key) + delta)

    def trained(self) -> list[tuple[SkillDef, int]]:
        """Skills the character actually has, best first."""
        pairs = [(SKILLS[k], r) for k, r in self.ranks.items() if r > 0]
        return sorted(pairs, key=lambda pair: (-pair[1], pair[0].label))

    def label(self, key: str) -> str:
        return skill_label(self.get(key))

    def copy(self) -> "Skills":
        return Skills(ranks=dict(self.ranks))
