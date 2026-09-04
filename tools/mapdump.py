"""Print a generated area as ASCII, for tuning the generator.

    python tools/mapdump.py            # a random seed
    python tools/mapdump.py 1234       # a specific one
    python tools/mapdump.py 1234 plains

Each cell shows the room's role; corridors are drawn between linked rooms.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lechery.content.game import new_game
from lechery.world import Role, World

GLYPHS = {
    Role.ENTRANCE: "@",
    Role.EXIT: ">",
    Role.BOSS: "!",
    Role.TREASURE: "$",
    Role.COMBAT: "x",
    Role.SET_PIECE: "*",
    Role.HAVEN: "^",
    Role.PASSAGE: ".",
}


def dump(world: World, area_id: str) -> str:
    area = world.area(area_id)
    placed = {room.position: room for room in area if room.position is not None}
    if not placed:
        return f"{area.name}: no positioned rooms"

    xs = [p[0] for p in placed]
    ys = [p[1] for p in placed]
    lines = []
    for y in range(min(ys), max(ys) + 1):
        cells, links = "", ""
        for x in range(min(xs), max(xs) + 1):
            room = placed.get((x, y))
            cells += GLYPHS.get(room.role, "?") if room else " "
            cells += "-" if room and room.exit_for("east") else " "
            links += "|" if room and room.exit_for("south") else " "
            links += " "
        lines.append(cells.rstrip())
        lines.append(links.rstrip())
    return "\n".join(line for line in lines[:-1])


def main(argv: list[str]) -> int:
    seed = int(argv[0]) if argv else None
    world = new_game(seed)
    only = argv[1] if len(argv) > 1 else None

    print(f"seed {world.seed}")
    for area in world.areas.values():
        if only and area.id != only:
            continue
        print(f"\n{area.name}  ({len(area)} rooms)")
        print(dump(world, area.id))
    print("\n" + "  ".join(f"{g} {r.value}" for r, g in GLYPHS.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
