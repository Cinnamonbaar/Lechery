"""Who you were, before.

The isekai premise makes the backstory do double duty: it is the character's
history *and* an explanation for why they are competent at anything at all
in a world they have never been in. So each one grants what it plausibly
would -- a nurse knows medicine, and knowing medicine is worth exactly as
much here as it was there.

Each backstory also carries the line the game opens on. That line is why
they are content rather than data: a table of stat bonuses is not a
character, and the sentence is doing most of the work.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..stats import Skills, Stat, StatBlock


@dataclass(frozen=True)
class Backstory:
    id: str
    name: str

    #: One line under the name in the picker.
    tagline: str

    #: What the player reads before choosing.
    description: str

    #: Stat adjustments applied on top of the baseline.
    stats: dict[Stat, int] = field(default_factory=dict)

    #: Starting skill ranks.
    skills: dict[str, int] = field(default_factory=dict)

    #: Logged when the game begins. The one piece of prose the player has
    #: before the world says anything.
    opening: str = ""

    def apply(self, stats: StatBlock, skills: Skills) -> None:
        for stat, delta in self.stats.items():
            stats.adjust(stat, delta)
        for key, rank in self.skills.items():
            skills.set(key, rank)


BACKSTORIES: tuple[Backstory, ...] = (
    Backstory(
        id="student",
        name="The Student",
        tagline="Two exams from a life you had not chosen yet.",
        description=(
            "You were good at the parts of school that could be studied for, "
            "which is most of them. You had read a great deal and done very "
            "little, and were beginning to suspect the two were related."
        ),
        stats={Stat.WITS: 2, Stat.RESOLVE: 1},
        skills={"lore": 2, "arcana": 1},
        opening=(
            "The last thing you remember is a train platform, and being late, "
            "and the particular grey of a morning you had every intention of "
            "surviving unremarkably."
        ),
    ),
    Backstory(
        id="nurse",
        name="The Nurse",
        tagline="Long shifts, bad coffee, and a very steady hand.",
        description=(
            "Twelve-hour shifts taught you what panic looks like in other "
            "people and how little use it is in yourself. You have seen worse "
            "than most of what this place has shown you so far."
        ),
        stats={Stat.WITS: 1, Stat.RESOLVE: 2},
        skills={"medicine": 3, "composure": 1},
        opening=(
            "You had just come off shift. You remember thinking, with real "
            "feeling, that you would sleep for a week — and then the corridor "
            "went white, and stayed white, and was not a corridor."
        ),
    ),
    Backstory(
        id="athlete",
        name="The Athlete",
        tagline="A body trained for a sport that does not exist here.",
        description=(
            "Years of early mornings gave you a body that does what it is "
            "told and a tolerance for discomfort that has already proved more "
            "useful than the sport ever was."
        ),
        stats={Stat.VIGOUR: 2, Stat.GRACE: 1, Stat.RESOLVE: 1},
        skills={"athletics": 3, "endurance": 1},
        opening=(
            "You were running. You remember the burn in your legs, and the "
            "turn in the road, and then no road at all — and the burn still "
            "there, in a body that had not stopped moving."
        ),
    ),
    Backstory(
        id="delinquent",
        name="The Delinquent",
        tagline="Expelled twice. Neither time unfairly.",
        description=(
            "You were not good at being told things. You were good at being "
            "hit and remaining standing, and at knowing which people in a "
            "room were about to become a problem."
        ),
        stats={Stat.VIGOUR: 2, Stat.PRESENCE: 1, Stat.RESOLVE: 1},
        skills={"brawling": 3, "insight": 1},
        opening=(
            "There was an argument, and then there was a fight, and then "
            "there was a stairwell that went considerably further down than "
            "any stairwell in that building had before."
        ),
    ),
    Backstory(
        id="office",
        name="The Salarywoman",
        tagline="Fourteen years in a company that will not notice you are gone.",
        description=(
            "You spent your working life managing people who outranked you "
            "into decisions they believed were theirs. It is a skill. Nobody "
            "ever calls it one."
        ),
        stats={Stat.PRESENCE: 2, Stat.WITS: 1, Stat.RESOLVE: 1},
        skills={"persuasion": 3, "insight": 1},
        opening=(
            "You worked late, as usual. You took the lift down, as usual. It "
            "kept going, which was not usual, and it went on not being usual "
            "for a considerable time."
        ),
    ),
    Backstory(
        id="artisan",
        name="The Artisan",
        tagline="Hands that know what they are doing without being asked.",
        description=(
            "You made things. Furniture, mostly, and latterly whatever people "
            "asked for. The work does not translate, but the hands do, and so "
            "does the patience."
        ),
        stats={Stat.WITS: 1, Stat.GRACE: 1, Stat.RESOLVE: 2},
        skills={"craft": 3, "survival": 1},
        opening=(
            "You were sanding a joint that would not sit true. You looked up "
            "because the light had changed, and it had changed because it was "
            "no longer coming through your window."
        ),
    ),
    Backstory(
        id="recluse",
        name="The Recluse",
        tagline="Four years indoors, and a suspicious familiarity with worlds like this.",
        description=(
            "You have read and watched and played a great deal about places "
            "very much like this one. It is not knowledge, exactly. But you "
            "know what a dungeon entrance looks like, which is more than most "
            "people pulled here can say."
        ),
        stats={Stat.WITS: 2, Stat.GRACE: 1, Stat.PRESENCE: -1, Stat.RESOLVE: 1},
        skills={"lore": 2, "stealth": 1, "arcana": 1},
        opening=(
            "You had not been outside in some time. You are aware of how this "
            "sounds. You are also aware, looking at the stone around you, that "
            "you recognise the genre — which is either very lucky or the worst "
            "possible sign."
        ),
    ),
)

BY_ID = {backstory.id: backstory for backstory in BACKSTORIES}


def backstory(backstory_id: str) -> Backstory:
    try:
        return BY_ID[backstory_id]
    except KeyError:
        raise KeyError(f"Unknown backstory {backstory_id!r}") from None
