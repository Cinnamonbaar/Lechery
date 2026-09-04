"""Room roles: what a place is *for*, independent of what it looks like.

Roles are the contract between layout generation and content. A generator
decides "this node is where the treasure goes" without knowing any prose; a
template pool answers "here are the rooms that can be a treasure room". They
are equally useful in handcrafted areas, where they give the rest of the game
a way to ask "where is the exit of this area" without hardcoding a room id.
"""

from __future__ import annotations

from enum import Enum


class Role(Enum):
    #: Where the player arrives when entering the area.
    ENTRANCE = "entrance"
    #: Leads onward to another area.
    EXIT = "exit"
    #: Ordinary connective tissue.
    PASSAGE = "passage"
    #: Expects an encounter.
    COMBAT = "combat"
    #: A reward, usually down a dead end.
    TREASURE = "treasure"
    #: A set piece: locked door, mechanism, scripted scene.
    SET_PIECE = "set_piece"
    #: The area's capstone encounter.
    BOSS = "boss"
    #: Safe ground: town, camp, save point.
    HAVEN = "haven"

    def __str__(self) -> str:
        return self.value
