"""The message log: what the game has told the player, in order.

Model-side and pygame-free. The log is a real transcript rather than a
scratch buffer of the last few lines, because the right bar shows history
and the player can scroll back through it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterator


class Kind(Enum):
    #: A room or area name; rendered as a heading.
    TITLE = "title"
    #: Descriptive prose.
    PROSE = "prose"
    #: Something that happened.
    EVENT = "event"
    #: Out-of-fiction notes: seeds, hints, debug.
    SYSTEM = "system"


@dataclass(frozen=True)
class Entry:
    text: str
    kind: Kind = Kind.EVENT


@dataclass
class MessageLog:
    """An append-only transcript, capped so a long session cannot grow it
    without bound. The cap is generous: scrollback is the point."""

    limit: int = 500
    entries: list[Entry] = field(default_factory=list)

    def add(self, text: str, kind: Kind = Kind.EVENT) -> Entry:
        entry = Entry(text=text, kind=kind)
        self.entries.append(entry)
        if len(self.entries) > self.limit:
            del self.entries[: len(self.entries) - self.limit]
        return entry

    def title(self, text: str) -> Entry:
        return self.add(text, Kind.TITLE)

    def prose(self, text: str) -> Entry:
        return self.add(text, Kind.PROSE)

    def system(self, text: str) -> Entry:
        return self.add(text, Kind.SYSTEM)

    def __iter__(self) -> Iterator[Entry]:
        return iter(self.entries)

    def __len__(self) -> int:
        return len(self.entries)
