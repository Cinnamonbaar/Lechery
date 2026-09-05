/** Actors: anything that occupies space and moves through it. */

import { moveAndCollide, type Point } from "./space/collision";
import type { TileMap } from "./space/tiles";
import { type Character, defaultCharacter } from "./traits/character";

/**
 * A body in the world.
 *
 * Positions are in tile units, not pixels: the renderer scales. Keeping game
 * units independent of the tile pixel size means changing the zoom never
 * changes the physics.
 */
export class Actor {
  position: Point = [0, 0];
  /** Half width and half height of the collision box. */
  halfExtents: Point = [0.3, 0.3];
  /** Tiles per second at full input. */
  speed = 6;
  /** Facing, in radians. 0 is east, growing clockwise (screen y is down). */
  facing = 0;
  velocity: Point = [0, 0];
  /** Id of the room the actor is currently standing in, if known. */
  roomId: string | null = null;

  constructor(public name = "actor") {}

  /**
   * Move along `direction` for `dt` seconds. Returns whether it moved.
   *
   * `direction` need not be normalised; it is, here, so that holding two keys
   * does not grant diagonal speed.
   */
  move(tilemap: TileMap, direction: Point, dt: number): boolean {
    const magnitude = Math.hypot(direction[0], direction[1]);
    if (magnitude === 0) {
      this.velocity = [0, 0];
      return false;
    }

    const dx = direction[0] / magnitude;
    const dy = direction[1] / magnitude;
    const step = this.speed * dt;
    this.velocity = [dx * this.speed, dy * this.speed];
    this.facing = Math.atan2(dy, dx);

    const before = this.position;
    const [moved] = moveAndCollide(tilemap, this.position, this.halfExtents, [
      dx * step,
      dy * step,
    ]);
    this.position = moved;
    return moved[0] !== before[0] || moved[1] !== before[1];
  }

  get tile(): readonly [number, number] {
    return [Math.floor(this.position[0]), Math.floor(this.position[1])];
  }
}

/**
 * The player character.
 *
 * Rendered as an anonymous grey silhouette on the top-down map -- the
 * character's actual appearance changes constantly and belongs to the
 * paperdoll view, not here.
 */
export class Player extends Actor {
  /**
   * Rooms the player has stood in, for map drawing and for prose that should
   * only fire once.
   */
  readonly seenRooms = new Set<string>();

  constructor(public character: Character = defaultCharacter()) {
    super("player");
    this.speed = 6.5;
    this.halfExtents = [0.28, 0.28];
  }
}
