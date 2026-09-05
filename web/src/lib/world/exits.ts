/** Exits: the directed edges between rooms. */

import { asKey, Direction, directionLabel, isDirection } from "./direction";

/**
 * A gate is any callable that inspects the travelling actor and decides
 * whether passage is allowed. `actor` is deliberately loose for now -- there
 * is no Player type yet, and exits should not be the reason one gets designed
 * prematurely.
 */
export type Gate = (actor: unknown) => boolean;

export interface ExitOptions {
  label?: string;
  blockedMessage?: string;
  hidden?: boolean;
  gate?: Gate | null;
}

/**
 * A one-way connection from one room to another.
 *
 * Two-way passages are two Exit objects; see `Room.connect`. Keeping them
 * one-way means a passage can be asymmetric (you can drop down a shaft but
 * not climb back up) without a special case.
 */
export class Exit {
  /** Player-facing label. Defaults to the key's own wording. */
  label: string | null;
  /** Shown instead of travelling when the exit is barred. */
  blockedMessage: string;
  /** Hidden exits are traversable but not listed until discovered. */
  hidden: boolean;
  /** Optional predicate; when it returns false the exit is barred. */
  gate: Gate | null;

  constructor(
    /**
     * Id of the destination room. Stored as an id rather than an object so
     * content modules can reference rooms that do not exist yet.
     */
    readonly target: string,
    /** How the exit is addressed: a Direction, or a free-form verb. */
    readonly key: Direction | string = Direction.NORTH,
    options: ExitOptions = {},
  ) {
    this.label = options.label ?? null;
    this.blockedMessage = options.blockedMessage ?? "You can't go that way.";
    this.hidden = options.hidden ?? false;
    this.gate = options.gate ?? null;
  }

  get keyString(): string {
    return asKey(this.key);
  }

  get displayLabel(): string {
    if (this.label) return this.label;
    const key = String(this.key);
    if (isDirection(key)) return directionLabel(key);
    return key.charAt(0).toUpperCase() + key.slice(1);
  }

  /** Whether `actor` may currently use this exit. */
  isOpen(actor: unknown = null): boolean {
    return this.gate === null || Boolean(this.gate(actor));
  }

  /** Whether this exit should be listed in the UI. */
  isVisible(): boolean {
    return !this.hidden;
  }
}
