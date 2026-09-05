/**
 * Carving one room into its own tilemap.
 *
 * Each room is a screen. A room's map is a walled rectangle with a doorway cut
 * into each wall that faces a neighbour, so the map's shape is decided
 * entirely by the room's size and which exits it has -- nothing about a room's
 * map depends on where its neighbours ended up, which is what makes rooms
 * independent enough to generate lazily later.
 *
 * Rooms that fit the view are framed whole; rooms larger than it scroll. That
 * is one carver, not two: the difference lives in the room's authored size.
 */

import { asKey, Direction } from "../world/direction";
import type { Room } from "../world/room";
import type { Rng } from "../generation/rng";
import { Tile, TileMap } from "./tiles";

/** Tile size of a room that fills one screen, walls included. */
export const DEFAULT_ROOM_SIZE: readonly [number, number] = [19, 13];

/**
 * How many interior pillars a room may scatter. A single 1x1 obstacle in an
 * open rectangle can never wall the room off -- you always go around -- so
 * this needs no connectivity check as long as they stay off the doorway
 * approaches, which `interiorCells` guarantees.
 */
export const PILLARS: readonly [number, number] = [0, 4];

/** How many breast-trap tiles a room may hold. Only tagged rooms get them. */
export const TRAPS: readonly [number, number] = [1, 3];

/**
 * Compass directions can be cut into a wall; anything else (an "up", a
 * "scramble down") is not a wall direction and becomes a portal instead.
 */
export const WALL_DIRECTIONS = [
  Direction.NORTH,
  Direction.SOUTH,
  Direction.EAST,
  Direction.WEST,
] as const;

/** Which way is "into the room" from a doorway in each wall. */
const INWARD: Record<string, readonly [number, number]> = {
  north: [0, 1],
  south: [0, -1],
  east: [-1, 0],
  west: [1, 0],
};

/** A gap in a room's wall leading to another room. */
export class Doorway {
  constructor(
    readonly direction: Direction,
    /** The threshold tile at the centre of the gap, in room tile space. */
    readonly tile: readonly [number, number],
    readonly targetRoomId: string,
    /**
     * Every tile of the gap. A doorway triggers on a body *overlapping* one
     * of these rather than centring on it, so the transition fires as the
     * player reaches the threshold.
     */
    readonly cells: readonly (readonly [number, number])[] = [],
    readonly width = 3,
  ) {}

  get key(): string {
    return this.direction;
  }

  /**
   * Where an arriving player stands: inside the room, off the door.
   *
   * Landing on the threshold itself would re-trigger the transition and
   * bounce the player back where they came from.
   */
  spawnTile(inset = 2): readonly [number, number] {
    const [dx, dy] = INWARD[this.direction] ?? [0, 0];
    return [this.tile[0] + dx * inset, this.tile[1] + dy * inset];
  }
}

/** One room's floorplan. */
export class RoomMap {
  constructor(
    readonly roomId: string,
    readonly tilemap: TileMap,
    readonly doorways: Map<string, Doorway>,
  ) {}

  get size(): readonly [number, number] {
    return [this.tilemap.width, this.tilemap.height];
  }

  get center(): readonly [number, number] {
    return [Math.floor(this.tilemap.width / 2), Math.floor(this.tilemap.height / 2)];
  }

  /**
   * The doorway a body at `position` is standing in, if any.
   *
   * Overlap rather than containment, so the transition fires the moment the
   * player reaches the threshold rather than once their centre is over it.
   */
  doorwayTouching(
    position: readonly [number, number],
    halfExtents: readonly [number, number],
  ): Doorway | null {
    const left = Math.floor(position[0] - halfExtents[0]);
    const right = Math.floor(position[0] + halfExtents[0]);
    const top = Math.floor(position[1] - halfExtents[1]);
    const bottom = Math.floor(position[1] + halfExtents[1]);

    for (const doorway of this.doorways.values()) {
      for (const [cx, cy] of doorway.cells) {
        if (cx >= left && cx <= right && cy >= top && cy <= bottom) return doorway;
      }
    }
    return null;
  }
}

/** Cut a gap of `width` tiles into the middle of one wall. */
function cutDoorway(
  tilemap: TileMap,
  direction: Direction,
  targetRoomId: string,
  width: number,
  roomId: string,
): Doorway {
  const half = Math.floor(width / 2);
  const midX = Math.floor(tilemap.width / 2);
  const midY = Math.floor(tilemap.height / 2);

  let tile: readonly [number, number];
  const cells: [number, number][] = [];

  if (direction === Direction.NORTH) {
    tile = [midX, 0];
    for (let o = -half; o <= half; o += 1) cells.push([midX + o, 0]);
  } else if (direction === Direction.SOUTH) {
    tile = [midX, tilemap.height - 1];
    for (let o = -half; o <= half; o += 1) cells.push([midX + o, tilemap.height - 1]);
  } else if (direction === Direction.WEST) {
    tile = [0, midY];
    for (let o = -half; o <= half; o += 1) cells.push([0, midY + o]);
  } else {
    tile = [tilemap.width - 1, midY];
    for (let o = -half; o <= half; o += 1) cells.push([tilemap.width - 1, midY + o]);
  }

  for (const [x, y] of cells) tilemap.set(x, y, Tile.DOORWAY, roomId);
  return new Doorway(direction, tile, targetRoomId, cells, width);
}

/**
 * Floor tiles safe to decorate: two in from every wall.
 *
 * Keeping a two-tile border clear means a decoration is never adjacent to a
 * wall or a doorway, so the path from any door into the room stays open
 * however the interior is filled.
 */
function interiorCells(tilemap: TileMap): [number, number][] {
  const cells: [number, number][] = [];
  for (let y = 3; y < tilemap.height - 3; y += 1) {
    for (let x = 3; x < tilemap.width - 3; x += 1) {
      if (tilemap.get(x, y) === Tile.FLOOR) cells.push([x, y]);
    }
  }
  return cells;
}

function scatter(
  tilemap: TileMap,
  roomId: string,
  cells: [number, number][],
  rng: Rng,
  range: readonly [number, number],
  tile: Tile,
): void {
  const count = Math.min(rng.int(range[0], range[1]), cells.length);
  for (let index = 0; index < count; index += 1) {
    const cell = cells.pop();
    if (!cell) return;
    tilemap.set(cell[0], cell[1], tile, roomId);
  }
}

export interface CarveOptions {
  defaultSize?: readonly [number, number];
  doorWidth?: number;
}

/** Build the tilemap for a single room, doorways and all. */
export function carveRoom(
  room: Room,
  rng: Rng,
  { defaultSize = DEFAULT_ROOM_SIZE, doorWidth = 3 }: CarveOptions = {},
): RoomMap {
  const [width, height] = room.size ?? defaultSize;

  const tilemap = new TileMap(width, height, Tile.VOID);
  tilemap.fillRect(1, 1, width - 2, height - 2, Tile.FLOOR, room.id);
  tilemap.outlineRect(0, 0, width, height, Tile.WALL, room.id);

  const doorways = new Map<string, Doorway>();
  for (const direction of WALL_DIRECTIONS) {
    const exit = room.exitFor(direction);
    if (!exit) continue;
    doorways.set(
      asKey(direction),
      cutDoorway(tilemap, direction, exit.target, doorWidth, room.id),
    );
  }

  // Interior variation, drawn from cells kept clear of the walls and the
  // doorway approaches. Safe rooms are left plain; a town square full of
  // pillars reads as rubble, not a town.
  if (!room.hasTag("safe")) {
    const cells = rng.shuffle(interiorCells(tilemap));
    scatter(tilemap, room.id, cells, rng, PILLARS, Tile.WALL);
    if (room.hasTag("trapped")) {
      scatter(tilemap, room.id, cells, rng, TRAPS, Tile.TRAP);
    }
  }

  return new RoomMap(room.id, tilemap, doorways);
}
