/**
 * The running game: world, floorplans, and the player moving through them.
 *
 * Everything the UI needs lives here, and none of it touches the DOM. A test
 * can spawn a session, walk the player through a dungeon and assert on where
 * they ended up, at no cost.
 */

import { Player } from "./actor";
import { newWorld, START_AREA } from "./content/game";
import { Kind, MessageLog } from "./log";
import { describeChange, describeReadShift } from "./narration";
import { type Level, type RoomMap, Tile } from "./space";
import type { Point } from "./space/collision";
import type { Character } from "./traits/character";
import type { Change } from "./traits/traits";
import type { Direction, Room, World } from "./world";

/** One playthrough. */
export class Session {
  level: Level;
  readonly log = new MessageLog();
  /**
   * The last presentation the player was told about, so a shift is reported
   * once when it happens rather than every frame.
   */
  private lastRead: string;

  constructor(
    readonly world: World,
    readonly levels: Map<string, Level>,
    readonly player: Player,
  ) {
    const start = levels.get(START_AREA);
    if (!start) throw new Error(`No level built for the start area ${START_AREA}`);
    this.level = start;

    // Transformations narrate themselves wherever they are triggered from,
    // rather than every caller remembering to log.
    this.player.character.traits.onChange = (change) => this.narrateChange(change);
    this.lastRead = this.player.character.presentation().label;

    const entry = this.world.area(START_AREA).entryRoom;
    if (!entry) throw new Error(`Area ${START_AREA} has no entry room`);
    this.arrive(entry.id);
    this.player.position = [...this.level.spawnCenter(entry.id)] as Point;
  }

  static newGame(seed: number | null = null, character?: Character): Session {
    const { world, levels } = newWorld(seed);
    const player = character ? new Player(character) : new Player();
    return new Session(world, levels, player);
  }

  // -- frame --------------------------------------------------------------

  get roomMap(): RoomMap {
    if (this.player.roomId === null) throw new Error("The player is nowhere");
    return this.level.mapFor(this.player.roomId);
  }

  /** Advance one frame. `direction` is raw input, need not be unit. */
  update(direction: Point, dt: number): void {
    this.player.move(this.roomMap.tilemap, direction, dt);
    this.checkTrap();
    this.checkDoorway();
    this.checkPortal();
  }

  /**
   * Spring a trap the player is standing on, then spend it.
   *
   * Checked before the doorway so a trap on the way out still fires, and the
   * tile becomes plain floor so it triggers once per step, not every frame the
   * body overlaps it. The bust change narrates itself through the trait hook.
   */
  private checkTrap(): void {
    const tilemap = this.roomMap.tilemap;
    const x = Math.floor(this.player.position[0]);
    const y = Math.floor(this.player.position[1]);
    if (tilemap.get(x, y) !== Tile.TRAP) return;
    tilemap.set(x, y, Tile.FLOOR);
    this.log.add("The tile gives beneath you with a soft click.", Kind.EVENT);
    this.player.character.adjust("bust", 1);
  }

  /**
   * Transition when the player stands in a doorway.
   *
   * Doorways are walkable, so the player crosses the threshold and is moved;
   * they never get stuck standing in one, because the far side spawns them
   * inset from the matching door.
   */
  private checkDoorway(): void {
    const doorway = this.roomMap.doorwayTouching(
      this.player.position,
      this.player.halfExtents,
    );
    if (!doorway) return;
    this.enterRoom(doorway.targetRoomId, doorway.direction);
  }

  private checkPortal(): void {
    if (this.player.roomId === null) return;
    const portal = this.level.portalAt(this.player.roomId, this.player.position);
    if (portal) this.travelTo(portal.targetRoomId);
  }

  // -- travel -------------------------------------------------------------

  /** Walk into an adjoining room in the same area. */
  enterRoom(roomId: string, arrivingFrom: Direction | null = null): void {
    this.arrive(roomId);
    const spawn =
      arrivingFrom === null
        ? this.level.spawnCenter(roomId)
        : this.level.spawnFrom(roomId, arrivingFrom);
    this.player.position = [...spawn] as Point;
  }

  /** Move to a room in another area, via a portal or a script. */
  travelTo(roomId: string): void {
    const room = this.world.room(roomId);
    if (room.areaId === null) {
      throw new Error(`Room ${JSON.stringify(roomId)} belongs to no area`);
    }

    if (room.areaId !== this.level.id) {
      const area = this.world.areaOf(room);
      if (area) this.log.system(area.name);
    }
    const level = this.levels.get(room.areaId);
    if (!level) throw new Error(`No level built for area ${room.areaId}`);
    this.level = level;
    this.arrive(roomId);
    this.player.position = [...this.level.spawnCenter(roomId)] as Point;
  }

  /**
   * Enter a room, and narrate it.
   *
   * The name is logged every time, so scrollback reads as a route. The prose
   * only on a first visit: repeating a paragraph the player has already read
   * trains them to stop reading the log at all.
   */
  private arrive(roomId: string): void {
    const room = this.world.room(roomId);
    const firstTime = !this.player.seenRooms.has(roomId);
    this.player.roomId = roomId;
    this.player.seenRooms.add(roomId);
    this.world.place(room, this.player);

    if (room.name) this.log.title(room.name);
    if (firstTime) {
      const description = room.describe(this.player);
      if (description) this.log.prose(description);
    }
  }

  private narrateChange(change: Change): void {
    const character = this.player.character;
    const line = describeChange(change, character);
    if (line) this.log.add(line, Kind.EVENT);
    this.checkReadShift();
  }

  /**
   * Report when the body has crossed into reading differently.
   *
   * Separate from the trait change itself: growing a chest and being taken for
   * a woman because of it are two events, and the second is the one the game
   * is about.
   */
  private checkReadShift(): void {
    const character = this.player.character;
    const current = character.presentation().label;
    if (current === this.lastRead) return;
    const line = describeReadShift(this.lastRead, current, character);
    this.lastRead = current;
    if (line) this.log.add(line, Kind.EVENT);
  }

  // -- state --------------------------------------------------------------

  get room(): Room | null {
    return this.world.currentRoom;
  }

  say(line: string, kind: Kind = Kind.EVENT): void {
    this.log.add(line, kind);
  }
}
