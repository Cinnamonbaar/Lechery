/**
 * Turning trait changes into sentences.
 *
 * Generic by design: this is the fallback so that *any* transformation reads
 * as something rather than nothing. Scenes that want a specific line should
 * write one and log it themselves -- content beats a template every time.
 *
 * Changes that stay inside a band are narrated more quietly than ones that
 * cross out of it, because "you are a little taller" and "you are tall now"
 * are different events.
 */

import type { Character } from "./traits/character";
import { grew, type Change, type TraitKey } from "./traits/traits";

/** Verb pairs per trait: [grew, shrank]. */
const VERBS: Partial<Record<TraitKey, readonly [string, string]>> = {
  height: ["You stand a little taller.", "You feel yourself shrink."],
  bust: ["Your chest feels heavier.", "Your chest feels lighter."],
  phallus: [
    "There is more of you than there was.",
    "There is less of you than there was.",
  ],
  age: ["The years settle heavier on you.", "The years lift from you."],
};

/**
 * Sentences for a change that crosses into a new band, where the label is
 * worth stating outright.
 */
const CROSSINGS: Partial<Record<TraitKey, (label: string) => string>> = {
  height: (label) => `You are ${label} now.`,
  bust: (label) => `Your chest has become ${label}.`,
  age: (label) => `You have become ${label}.`,
};

const numeric = (value: unknown): number =>
  typeof value === "number" ? value : 0;

const appeared = (change: Change): boolean =>
  numeric(change.before) < 1 && numeric(change.after) >= 1;

const vanished = (change: Change): boolean =>
  numeric(change.before) >= 1 && numeric(change.after) < 1;

/** A line for a trait change, or null if it does not deserve one. */
export function describeChange(
  change: Change,
  character: Character,
): string | null {
  if (change.key === "name") {
    return `You are called ${String(change.after)} now.`;
  }

  if (change.key === "hair_colour" || change.key === "eye_colour") {
    const name = character.traits.label(change.key);
    return change.key === "eye_colour"
      ? `Your eyes are now ${name}.`
      : `Your hair is now ${name}.`;
  }

  if (change.key === "phallus" && appeared(change)) {
    return "Something that was not there before is.";
  }
  if (change.key === "phallus" && vanished(change)) {
    return "What was there is not, any more.";
  }

  const crossing = CROSSINGS[change.key];
  if (change.crossedBand && crossing) {
    return crossing(character.traits.label(change.key));
  }

  const verbs = VERBS[change.key];
  if (!verbs) return null;
  return grew(change) ? verbs[0] : verbs[1];
}

/**
 * How it lands when the way strangers read you shifts. Phrased from the
 * character's side rather than an observer's: nobody is in the room when a
 * transformation happens, so what changes in the moment is what you expect to
 * happen next time someone looks.
 */
const READ_SHIFTS: Record<string, string> = {
  "androgynous>feminine":
    "You would be taken for a woman now, by anyone not looking twice.",
  "androgynous>masculine":
    "You would be taken for a man now, by anyone not looking twice.",
  "feminine>androgynous":
    "It is no longer obvious, at a glance, what you are.",
  "masculine>androgynous":
    "It is no longer obvious, at a glance, what you are.",
  "feminine>masculine":
    "Strangers would see a man where they used to see a woman.",
  "masculine>feminine":
    "Strangers would see a woman where they used to see a man.",
};

/**
 * A line for the way the character is read having changed.
 *
 * Returned separately from the trait change that caused it: growing a chest
 * and being read differently because of it are two events, and the second is
 * the one this game is actually about.
 */
export function describeReadShift(
  before: string,
  after: string,
  character: Character,
): string | null {
  const line = READ_SHIFTS[`${before}>${after}`];
  if (!line) return null;
  if (!character.readMatchesIdentity) {
    // Worth saying outright when the mismatch is the new state, since it is
    // the thing the player will be living with.
    return `${line} It is not what you are.`;
  }
  return line;
}
