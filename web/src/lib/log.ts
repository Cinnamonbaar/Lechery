/**
 * The message log: what the game has told the player, in order.
 *
 * A real transcript rather than a scratch buffer of the last few lines,
 * because the right bar shows history and the player can scroll back.
 */

export const Kind = {
  /** A room or area name; rendered as a heading. */
  TITLE: "title",
  /** Descriptive prose. */
  PROSE: "prose",
  /** Something that happened. */
  EVENT: "event",
  /** Out-of-fiction notes: seeds, hints, debug. */
  SYSTEM: "system",
} as const;

export type Kind = (typeof Kind)[keyof typeof Kind];

export interface Entry {
  readonly text: string;
  readonly kind: Kind;
  /** Monotonic id, so a UI list can key on something stable. */
  readonly id: number;
}

/**
 * An append-only transcript, capped so a long session cannot grow it without
 * bound. The cap is generous: scrollback is the point.
 */
export class MessageLog {
  entries: Entry[] = [];
  private nextId = 1;
  /** Called after every append, so a view can react without polling. */
  onAppend: ((entry: Entry) => void) | null = null;

  constructor(readonly limit = 500) {}

  add(text: string, kind: Kind = Kind.EVENT): Entry {
    const entry: Entry = { text, kind, id: this.nextId++ };
    this.entries.push(entry);
    if (this.entries.length > this.limit) {
      this.entries = this.entries.slice(this.entries.length - this.limit);
    }
    this.onAppend?.(entry);
    return entry;
  }

  title(text: string): Entry {
    return this.add(text, Kind.TITLE);
  }

  prose(text: string): Entry {
    return this.add(text, Kind.PROSE);
  }

  system(text: string): Entry {
    return this.add(text, Kind.SYSTEM);
  }

  get length(): number {
    return this.entries.length;
  }

  [Symbol.iterator](): IterableIterator<Entry> {
    return this.entries[Symbol.iterator]();
  }
}
