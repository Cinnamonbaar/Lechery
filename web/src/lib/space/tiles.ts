/**
 * Tilemaps: the walkable geometry of an area.
 *
 * Geometry, not rendering. The renderer reads it; so does collision; so do
 * tests.
 */

export const Tile = {
  /** Outside the level. Solid, and drawn as nothing. */
  VOID: 0,
  FLOOR: 1,
  WALL: 2,
  /** Walkable, but marks the threshold between two rooms. */
  DOORWAY: 3,
  /**
   * Walkable. Springs an effect the first time it is stood on, then spends
   * itself and becomes plain floor.
   */
  TRAP: 4,
} as const;

export type Tile = (typeof Tile)[keyof typeof Tile];

export function isSolid(tile: Tile): boolean {
  return tile === Tile.VOID || tile === Tile.WALL;
}

/**
 * A rectangular grid of tiles, with a room id recorded per tile.
 *
 * The per-tile room id is what lets the game answer "which room is the player
 * standing in" every frame without any geometry tests -- one array lookup.
 * That question drives room descriptions, encounters and music, so it needs
 * to be cheap.
 */
export class TileMap {
  private readonly tiles: Tile[];
  private readonly roomIds: (string | null)[];

  constructor(
    readonly width: number,
    readonly height: number,
    fill: Tile = Tile.VOID,
  ) {
    this.tiles = new Array(width * height).fill(fill);
    this.roomIds = new Array(width * height).fill(null);
  }

  inBounds(x: number, y: number): boolean {
    return x >= 0 && x < this.width && y >= 0 && y < this.height;
  }

  /** Out-of-bounds reads return VOID, so callers need no bounds check. */
  get(x: number, y: number): Tile {
    if (!this.inBounds(x, y)) return Tile.VOID;
    return this.tiles[y * this.width + x]!;
  }

  set(x: number, y: number, tile: Tile, roomId: string | null = null): void {
    if (!this.inBounds(x, y)) return;
    const index = y * this.width + x;
    this.tiles[index] = tile;
    if (roomId !== null) this.roomIds[index] = roomId;
  }

  roomAt(x: number, y: number): string | null {
    if (!this.inBounds(x, y)) return null;
    return this.roomIds[y * this.width + x] ?? null;
  }

  isSolidAt(x: number, y: number): boolean {
    return isSolid(this.get(x, y));
  }

  isWalkable(x: number, y: number): boolean {
    return !this.isSolidAt(x, y);
  }

  fillRect(
    x: number,
    y: number,
    width: number,
    height: number,
    tile: Tile,
    roomId: string | null = null,
  ): void {
    for (let ty = y; ty < y + height; ty += 1) {
      for (let tx = x; tx < x + width; tx += 1) this.set(tx, ty, tile, roomId);
    }
  }

  outlineRect(
    x: number,
    y: number,
    width: number,
    height: number,
    tile: Tile,
    roomId: string | null = null,
  ): void {
    for (let tx = x; tx < x + width; tx += 1) {
      this.set(tx, y, tile, roomId);
      this.set(tx, y + height - 1, tile, roomId);
    }
    for (let ty = y; ty < y + height; ty += 1) {
      this.set(x, ty, tile, roomId);
      this.set(x + width - 1, ty, tile, roomId);
    }
  }

  count(tile: Tile): number {
    return this.tiles.reduce<number>(
      (total, value) => total + (value === tile ? 1 : 0),
      0,
    );
  }

  toString(): string {
    const glyphs: Record<Tile, string> = {
      [Tile.VOID]: " ",
      [Tile.FLOOR]: ".",
      [Tile.WALL]: "#",
      [Tile.DOORWAY]: "+",
      [Tile.TRAP]: "^",
    };
    const rows: string[] = [];
    for (let y = 0; y < this.height; y += 1) {
      let row = "";
      for (let x = 0; x < this.width; x += 1) row += glyphs[this.get(x, y)];
      rows.push(row);
    }
    return rows.join("\n");
  }
}
