/**
 * Levels: an Area plus the floorplan of each of its rooms.
 *
 * The Area answers "what is this room, and what is it for". The Level answers
 * "what does it look like underfoot, and where are its doors". Keeping them
 * apart means area content can be authored and tested with no geometry at all.
 */

import type { Rng } from "../generation/rng";
import type { Area } from "../world/area";
import { Direction, opposite } from "../world/direction";
import { carveRoom, DEFAULT_ROOM_SIZE, type RoomMap } from "./carve";

/**
 * A tile that moves the player elsewhere when stepped on.
 *
 * Doorways handle the four compass walls. A portal handles everything that is
 * not a wall direction -- a stair up out of the dungeon, a ladder down.
 * Without it, an area could be joined logically but not on foot.
 */
export interface Portal {
  readonly tile: readonly [number, number];
  readonly targetRoomId: string;
  readonly label: string;
}

const tileKey = (tile: readonly [number, number]): string => `${tile[0]},${tile[1]}`;

export class Level {
  readonly maps = new Map<string, RoomMap>();
  /** Portals per room id, keyed by the tile they occupy. */
  readonly portals = new Map<string, Map<string, Portal>>();

  constructor(readonly area: Area) {}

  get id(): string {
    return this.area.id;
  }

  mapFor(roomId: string): RoomMap {
    const found = this.maps.get(roomId);
    if (!found) throw new Error(`No carved map for room ${roomId}`);
    return found;
  }

  portalAt(roomId: string, position: readonly [number, number]): Portal | null {
    const room = this.portals.get(roomId);
    if (!room) return null;
    const key = tileKey([Math.floor(position[0]), Math.floor(position[1])]);
    return room.get(key) ?? null;
  }

  portalsIn(roomId: string): Portal[] {
    return [...(this.portals.get(roomId)?.values() ?? [])];
  }

  spawnCenter(roomId: string): readonly [number, number] {
    const [x, y] = this.mapFor(roomId).center;
    return [x + 0.5, y + 0.5];
  }

  /**
   * Where to stand on entering `roomId` through a given wall.
   *
   * `arrivingFrom` is the direction of travel, so entering while heading
   * north means coming in through this room's *south* wall.
   */
  spawnFrom(roomId: string, arrivingFrom: Direction): readonly [number, number] {
    const roomMap = this.mapFor(roomId);
    const doorway = roomMap.doorways.get(opposite(arrivingFrom));
    if (!doorway) return this.spawnCenter(roomId);
    const [x, y] = doorway.spawnTile();
    return [x + 0.5, y + 0.5];
  }

  /** Place a portal at the centre of a room. */
  addPortal(roomId: string, targetRoomId: string, label = ""): Portal {
    const tile = this.mapFor(roomId).center;
    const portal: Portal = { tile, targetRoomId, label };
    if (!this.portals.has(roomId)) this.portals.set(roomId, new Map());
    this.portals.get(roomId)!.set(tileKey(tile), portal);
    return portal;
  }
}

/**
 * Carve every room in an area.
 *
 * Note this takes only the Area: with rooms carved independently, the layout
 * is no longer needed once the exits are wired.
 */
export function buildLevel(
  area: Area,
  rng: Rng,
  defaultSize: readonly [number, number] = DEFAULT_ROOM_SIZE,
): Level {
  const level = new Level(area);
  for (const room of area) {
    level.maps.set(room.id, carveRoom(room, rng, { defaultSize }));
  }
  return level;
}
