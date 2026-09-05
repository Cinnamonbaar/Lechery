/**
 * Room templates: the content a layout node gets dressed in.
 *
 * A template is a recipe for a Room, not a Room. One template can produce many
 * rooms across many playthroughs, so it must not hold per-playthrough state --
 * `build` returns a fresh Room every time.
 */

import { Role } from "../world/roles";
import { Room } from "../world/room";
import type { Rng } from "./rng";

/**
 * Lets a template produce a Room subclass (a shop, a trap, a scripted scene)
 * instead of a plain Room.
 */
export type RoomFactory = (id: string, description: string) => Room;

export interface RoomTemplateOptions {
  /**
   * Description variants. One is chosen per room, so the same template used
   * twice in a dungeon does not read as copy-paste.
   */
  descriptions?: readonly string[];
  /** Roles this template may fill. Empty means "any role". */
  roles?: readonly Role[];
  /** Relative likelihood against other eligible templates. */
  weight?: number;
  /** A template with `unique` set appears at most once per area. */
  unique?: boolean;
  tags?: readonly string[];
  /**
   * Tile size of the room's map, walls included. Null uses the area default.
   * This is how a town is authored as a big scrolling space while a dungeon
   * room stays a single framed screen.
   */
  size?: readonly [number, number] | null;
  /** Builds a Room subclass when a plain Room will not do. */
  factory?: RoomFactory | null;
}

/** A recipe for one kind of room. */
export class RoomTemplate {
  readonly descriptions: readonly string[];
  readonly roles: ReadonlySet<Role>;
  readonly weight: number;
  readonly unique: boolean;
  readonly tags: readonly string[];
  readonly size: readonly [number, number] | null;
  readonly factory: RoomFactory | null;

  constructor(
    readonly id: string,
    readonly name: string,
    options: RoomTemplateOptions = {},
  ) {
    this.descriptions = options.descriptions ?? [];
    this.roles = new Set(options.roles ?? []);
    this.weight = options.weight ?? 1;
    this.unique = options.unique ?? false;
    this.tags = options.tags ?? [];
    this.size = options.size ?? null;
    this.factory = options.factory ?? null;
  }

  accepts(role: Role): boolean {
    return this.roles.size === 0 || this.roles.has(role);
  }

  build(roomId: string, role: Role, rng: Rng): Room {
    const description = this.descriptions.length ? rng.pick(this.descriptions) : "";
    const room = this.factory
      ? this.factory(roomId, description)
      : new Room(roomId, this.name, { description });
    room.role = role;
    room.size = this.size;
    room.tag(...this.tags);
    if (!room.flags.has("template")) room.flags.set("template", this.id);
    return room;
  }
}

/**
 * The set of templates available to one area.
 *
 * Selection is weighted-random among templates eligible for the node's role,
 * minus any already-used unique ones. Templates recently used are down-weighted
 * so a corridor of six identical rooms is unlikely without being forbidden.
 */
export class TemplatePool {
  /** Multiplier applied to a template used within the last few picks. */
  static readonly REPEAT_PENALTY = 0.25;
  /** How many recent picks the penalty remembers. */
  static readonly MEMORY = 3;

  readonly templates = new Map<string, RoomTemplate>();
  private usedUnique = new Set<string>();
  private recent: string[] = [];

  constructor(templates: readonly RoomTemplate[] = []) {
    for (const template of templates) this.add(template);
  }

  add(template: RoomTemplate): RoomTemplate {
    if (this.templates.has(template.id)) {
      throw new Error(`Duplicate template id ${template.id}`);
    }
    this.templates.set(template.id, template);
    return template;
  }

  get(id: string): RoomTemplate {
    const found = this.templates.get(id);
    if (!found) throw new Error(`No template ${id} in pool`);
    return found;
  }

  eligible(role: Role): RoomTemplate[] {
    return [...this.templates.values()].filter(
      (template) =>
        template.accepts(role) && !(template.unique && this.usedUnique.has(template.id)),
    );
  }

  pick(role: Role, rng: Rng): RoomTemplate {
    const candidates = this.eligible(role);
    if (!candidates.length) throw new Error(`No template in pool can fill role ${role}`);
    const weights = candidates.map(
      (template) =>
        template.weight *
        (this.recent.includes(template.id) ? TemplatePool.REPEAT_PENALTY : 1),
    );
    const chosen = rng.weighted(candidates, weights);
    this.mark(chosen);
    return chosen;
  }

  private mark(template: RoomTemplate): void {
    if (template.unique) this.usedUnique.add(template.id);
    this.recent.push(template.id);
    if (this.recent.length > TemplatePool.MEMORY) {
      this.recent = this.recent.slice(-TemplatePool.MEMORY);
    }
  }

  /** Forget usage history, so the pool can build another area. */
  reset(): void {
    this.usedUnique = new Set();
    this.recent = [];
  }
}
