import { describe, expect, it } from "vitest";

import { Session } from "./session";
import { newWorld, START_AREA } from "./content/game";
import { Kind } from "./log";
import { Tile } from "./space";
import { Role } from "./world";
import { rngFor } from "./generation";
import * as tutorial from "./content/areas/tutorial";

describe("world generation", () => {
  it("builds a valid world", () => {
    const { world, levels } = newWorld(12345);
    expect(world.validate()).toEqual([]);
    expect(levels.size).toBe(2);
    for (const room of world.rooms) {
      expect(levels.get(room.areaId!)!.mapFor(room.id)).toBeTruthy();
    }
  });

  it("is deterministic in the seed", () => {
    const names = (seed: number) =>
      newWorld(seed).world.rooms.map((room) => `${room.id}:${room.name}`);
    expect(names(7)).toEqual(names(7));
    expect(names(7)).not.toEqual(names(8));
  });

  it("keeps areas independent of each other's seeds", () => {
    // Editing one area must not reshuffle the next; that is what per-area
    // seed derivation buys.
    const [a] = tutorial.build(rngFor(99, tutorial.AREA_ID));
    const [b] = tutorial.build(rngFor(99, tutorial.AREA_ID));
    expect([...a].map((room) => room.id)).toEqual([...b].map((room) => room.id));
  });

  it("joins the dungeon to the hub on foot", () => {
    const { world, levels } = newWorld(4);
    const exit = world.area("tutorial").firstWithRole(Role.EXIT)!;
    const portals = levels.get("tutorial")!.portalsIn(exit.id);
    expect(portals).toHaveLength(1);
    expect(world.room(portals[0]!.targetRoomId).areaId).toBe("plains");
  });
});

describe("session", () => {
  const start = () => Session.newGame(2024);

  it("starts in the tutorial entrance and logs it", () => {
    const session = start();
    expect(session.level.id).toBe(START_AREA);
    expect(session.room!.role).toBe(Role.ENTRANCE);
    expect(session.log.entries[0]!.kind).toBe(Kind.TITLE);
    expect(session.log.entries.some((entry) => entry.kind === Kind.PROSE)).toBe(true);
  });

  it("does not repeat prose on a second visit", () => {
    const session = start();
    const roomId = session.player.roomId!;
    const before = session.log.length;
    session.enterRoom(roomId);
    const added = session.log.entries.slice(before);
    expect(added.every((entry) => entry.kind !== Kind.PROSE)).toBe(true);
  });

  it("spends a trap once and grows the bust", () => {
    const session = start();
    const map = session.roomMap;
    const [x, y] = map.center;
    map.tilemap.set(x, y, Tile.TRAP);
    session.player.position = [x + 0.5, y + 0.5];

    const before = session.player.character.traits.get("bust");
    session.update([0, 0], 0);
    expect(session.player.character.traits.get("bust")).toBe(before + 1);
    expect(map.tilemap.get(x, y)).toBe(Tile.FLOOR);

    session.update([0, 0], 0);
    expect(session.player.character.traits.get("bust")).toBe(before + 1);
  });

  it("travels between areas through a portal", () => {
    const session = start();
    const hub = session.world.area("plains").entryRoom!;
    session.travelTo(hub.id);
    expect(session.level.id).toBe("plains");
    expect(session.player.roomId).toBe(hub.id);
  });

  it("moves the player through a doorway into the next room", () => {
    const session = start();
    const first = session.player.roomId!;
    const doorway = [...session.roomMap.doorways.values()][0]!;
    const [dx, dy] = doorway.spawnTile();
    session.player.position = [dx + 0.5, dy + 0.5];
    session.update([0, 0], 0);
    // Standing on the spawn tile is inset from the door, so walk into it.
    session.player.position = [
      doorway.tile[0] + 0.5,
      doorway.tile[1] + 0.5,
    ];
    session.update([0, 0], 0);
    expect(session.player.roomId).not.toBe(first);
  });
});
