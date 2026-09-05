/** Rooms: a single place the player can occupy. */

import { asKey, Direction, opposite } from "./direction";
import { Exit, type ExitOptions } from "./exits";
import { Role } from "./roles";

/** Called when the player enters or leaves. */
export type RoomHook = (room: Room, actor: unknown) => void;

export interface RoomOptions {
  description?: string;
  role?: Role;
  size?: readonly [number, number] | null;
  position?: readonly [number, number] | null;
  tags?: Iterable<string>;
}

/**
 * One discrete place.
 *
 * Subclass this for rooms that need behaviour (a shop, a trap, an encounter
 * node). The base class deliberately knows nothing about combat, items or the
 * player -- it is geography and description only.
 */
export class Room {
  description: string;
  /** Id of the owning Area, set by `Area.add`. */
  areaId: string | null = null;
  /** What this room is for. Set by the generator, or by hand. */
  role: Role;
  /**
   * Tile dimensions of this room's map, walls included. Null takes the area's
   * default. A room larger than the screen scrolls; one that fits is framed
   * whole with a fixed camera.
   */
  size: readonly [number, number] | null;
  /** Grid position within its area, when it has one. */
  position: readonly [number, number] | null;
  /** Free-form markers content can query: "indoors", "safe", "water". */
  readonly tags: Set<string>;
  /** Per-room mutable state (switch thrown, chest looted, npc met). */
  readonly flags = new Map<string, unknown>();
  /** Exits keyed by their normalised key string. */
  readonly exits = new Map<string, Exit>();
  /** True once the player has entered at least once. */
  visited = false;

  onEnter: RoomHook | null = null;
  onExit: RoomHook | null = null;

  constructor(
    readonly id: string,
    readonly name: string,
    options: RoomOptions = {},
  ) {
    this.description = options.description ?? "";
    this.role = options.role ?? Role.PASSAGE;
    this.size = options.size ?? null;
    this.position = options.position ?? null;
    this.tags = new Set(options.tags ?? []);
  }

  // -- description --------------------------------------------------------

  /**
   * The prose for this room.
   *
   * Overridden by subclasses that vary their text by world state; the base
   * implementation is just the static description.
   */
  describe(_actor: unknown = null): string {
    return this.description;
  }

  // -- exits --------------------------------------------------------------

  /** Register an exit, replacing any existing one on the same key. */
  addExit(exit: Exit): Exit {
    this.exits.set(exit.keyString, exit);
    return exit;
  }

  /** Create a one-way exit from this room. */
  link(
    direction: Direction | string,
    target: string | Room,
    options: ExitOptions = {},
  ): Exit {
    const targetId = typeof target === "string" ? target : target.id;
    return this.addExit(new Exit(targetId, direction, options));
  }

  /**
   * Link two rooms both ways.
   *
   * The return exit uses the opposite direction unless `back` overrides it.
   * Only compass-style directions can be auto-reversed, which is why this
   * takes a Direction rather than a free-form key.
   */
  connect(
    direction: Direction,
    other: Room,
    options: ExitOptions & { back?: Direction } = {},
  ): [Exit, Exit] {
    const { back, ...rest } = options;
    const forward = this.link(direction, other, rest);
    const backward = other.link(back ?? opposite(direction), this, rest);
    return [forward, backward];
  }

  exitFor(key: Direction | string): Exit | undefined {
    return this.exits.get(asKey(key));
  }

  /** Exits the UI should offer: visible, in insertion order. */
  availableExits(): Exit[] {
    return [...this.exits.values()].filter((exit) => exit.isVisible());
  }

  // -- lifecycle ----------------------------------------------------------

  /** Called by the World after the player has been moved in. */
  enter(actor: unknown = null): void {
    const firstVisit = !this.visited;
    this.visited = true;
    if (firstVisit) this.onFirstEnter(actor);
    this.onEnter?.(this, actor);
  }

  /** Hook for subclasses; runs once, before `onEnter`. */
  onFirstEnter(_actor: unknown = null): void {}

  leave(actor: unknown = null): void {
    this.onExit?.(this, actor);
  }

  // -- tags ---------------------------------------------------------------

  hasTag(tag: string): boolean {
    return this.tags.has(tag);
  }

  tag(...tags: string[]): this {
    for (const tag of tags) this.tags.add(tag);
    return this;
  }
}
