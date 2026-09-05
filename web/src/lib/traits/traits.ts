/**
 * The trait model: what a character is made of, and how it changes.
 *
 * Every change goes through `set` or `adjust` and comes back as a Change
 * record. That is the point of the class: a transformation game needs to
 * narrate what moved and in which direction, and if content had to diff the
 * body by hand before and after every effect, half of it would forget.
 */

import type { Colour } from "./palette";
import { findColour } from "./palette";
import { MINIMUM_AGE, type Scale, scaleFor } from "./scale";

/** The traits a character has. Keyed so a typo is a compile error. */
export interface TraitValues {
  name: string;
  age: number;
  height: number;
  hair_colour: Colour;
  eye_colour: Colour;
  bust: number;
  phallus: number;
}

export type TraitKey = keyof TraitValues;

/** One trait moving from one value to another. */
export interface Change<K extends TraitKey = TraitKey> {
  readonly key: K;
  readonly before: TraitValues[K] | undefined;
  readonly after: TraitValues[K];
  /** +1 grew, -1 shrank, 0 changed without an order (a colour). */
  readonly direction: number;
  /**
   * Whether the change crossed into a different band -- "a bit taller"
   * versus "tall now". Content usually only wants to narrate the latter.
   */
  readonly crossedBand: boolean;
}

export function grew(change: Change): boolean {
  return change.direction > 0;
}

export function shrank(change: Change): boolean {
  return change.direction < 0;
}

/** What a trait is: how to validate it, and how to say it. */
interface TraitDef<K extends TraitKey = TraitKey> {
  readonly key: K;
  readonly label: string;
  /** Numeric traits name a Scale; the rest validate their own way. */
  readonly scale?: string;
  readonly clean: (value: unknown) => TraitValues[K];
}

function cleanName(value: unknown): string {
  const name = String(value ?? "").trim();
  if (!name) throw new Error("a character needs a name");
  return name.slice(0, 40);
}

function cleanAge(value: unknown): number {
  const age = Number(value);
  if (!Number.isFinite(age)) throw new Error("age must be a number");
  // Enforced here rather than only clamped, so a caller passing a child's
  // age gets an error instead of a silent correction they never notice.
  if (age < MINIMUM_AGE) throw new Error(`age must be at least ${MINIMUM_AGE}`);
  return Math.min(age, 90);
}

function cleanColour(value: unknown): Colour {
  if (value && typeof value === "object" && "rgb" in (value as Colour)) {
    return value as Colour;
  }
  return findColour(String(value));
}

function scaled(name: string) {
  return (value: unknown): number => {
    const scale = scaleFor(name)!;
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) throw new Error(`${name} must be a number`);
    return scale.clamp(numeric);
  };
}

export const TRAITS = {
  name: { key: "name", label: "Name", clean: cleanName },
  age: { key: "age", label: "Age", scale: "age", clean: cleanAge },
  height: { key: "height", label: "Height", scale: "height", clean: scaled("height") },
  hair_colour: { key: "hair_colour", label: "Hair", clean: cleanColour },
  eye_colour: { key: "eye_colour", label: "Eyes", clean: cleanColour },
  bust: { key: "bust", label: "Bust", scale: "bust", clean: scaled("bust") },
  phallus: { key: "phallus", label: "Phallus", scale: "phallus", clean: scaled("phallus") },
} satisfies { [K in TraitKey]: TraitDef<K> };

export type ChangeListener = (change: Change) => void;

/** A character's trait values, and the history of what changed them. */
export class Traits {
  private values = new Map<TraitKey, TraitValues[TraitKey]>();
  readonly history: Change[] = [];
  /**
   * Called with each Change. The session hooks this up to the log, so a
   * transformation narrates itself wherever it is triggered from.
   */
  onChange: ChangeListener | null = null;

  constructor(values: Partial<TraitValues> = {}) {
    for (const [key, value] of Object.entries(values)) {
      const definition = TRAITS[key as TraitKey];
      if (!definition) throw new Error(`Unknown trait ${JSON.stringify(key)}`);
      this.values.set(key as TraitKey, definition.clean(value));
    }
  }

  // -- reading ------------------------------------------------------------

  has(key: TraitKey): boolean {
    return this.values.has(key);
  }

  get<K extends TraitKey>(key: K): TraitValues[K] {
    const value = this.values.get(key);
    if (value === undefined) throw new Error(`Character has no trait ${key}`);
    return value as TraitValues[K];
  }

  maybe<K extends TraitKey>(key: K, fallback: TraitValues[K]): TraitValues[K] {
    const value = this.values.get(key);
    return value === undefined ? fallback : (value as TraitValues[K]);
  }

  scaleOf(key: TraitKey): Scale | undefined {
    const definition = TRAITS[key] as TraitDef;
    return definition.scale ? scaleFor(definition.scale) : undefined;
  }

  /** The word for a trait's current value: "tall", "ash blonde". */
  label(key: TraitKey): string {
    const value = this.get(key);
    const scale = this.scaleOf(key);
    if (scale) return scale.label(value as number);
    if (value && typeof value === "object" && "name" in value) return value.name;
    return String(value);
  }

  /** The value as prose would give it: "172cm (average height)". */
  describe(key: TraitKey): string {
    const value = this.get(key);
    const scale = this.scaleOf(key);
    if (scale) return scale.format(value as number);
    if (value && typeof value === "object" && "name" in value) return value.name;
    return String(value);
  }

  entries(): [TraitKey, TraitValues[TraitKey]][] {
    return [...this.values.entries()];
  }

  // -- writing ------------------------------------------------------------

  /** Set a trait. Returns the Change, or null if nothing moved. */
  set<K extends TraitKey>(key: K, value: unknown): Change<K> | null {
    const definition = TRAITS[key] as TraitDef<K> | undefined;
    if (!definition) throw new Error(`Unknown trait ${String(key)}`);

    const before = this.values.get(key) as TraitValues[K] | undefined;
    const after = definition.clean(value);
    if (before === after) return null;

    const scale = this.scaleOf(key);
    let direction = 0;
    let crossedBand = true;
    if (scale && before !== undefined) {
      const a = before as number;
      const b = after as number;
      direction = b > a ? 1 : b < a ? -1 : 0;
      crossedBand = scale.index(b) !== scale.index(a);
    } else if (before === undefined) {
      crossedBand = false; // the initial value is not a transformation
    }

    this.values.set(key, after);
    const change: Change<K> = { key, before, after, direction, crossedBand };
    if (before !== undefined) {
      this.history.push(change as Change);
      this.onChange?.(change as Change);
    }
    return change;
  }

  /** Move a numeric trait by `delta`. The usual transformation verb. */
  adjust(key: TraitKey, delta: number): Change | null {
    if (!this.scaleOf(key)) {
      throw new Error(`Trait ${key} is not numeric and cannot be adjusted`);
    }
    return this.set(key, (this.get(key) as number) + delta);
  }

  update(values: Partial<TraitValues>): Change[] {
    const changes: Change[] = [];
    for (const [key, value] of Object.entries(values)) {
      const change = this.set(key as TraitKey, value);
      if (change) changes.push(change as Change);
    }
    return changes;
  }
}
