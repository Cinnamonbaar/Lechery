/**
 * How a body reads to someone looking at it.
 *
 * This is a third axis, distinct from both identity and the body itself:
 *
 *   identity      what the character is. Only the player changes it.
 *   presentation  what the body reads as. Derived; nobody sets it directly.
 *   perception    what one observer concludes, given what they can see and
 *                 whether they already know you.
 *
 * They are allowed to disagree, and the disagreement is the point -- a game
 * about bodies changing under you is partly a game about being read wrongly.
 * Deriving identity from the body would erase that; so would deriving nothing
 * and having strangers politely use whatever pronouns you picked.
 *
 * Two rules the model enforces rather than leaves to content:
 *
 *   A signal only counts if the observer can see it. A stranger across a
 *   market is not reading anything under your clothes, so parts covered by
 *   clothing contribute nothing to presentation while dressed. Getting this
 *   wrong is not a balance problem, it is a modelling bug.
 *
 *   Knowing someone beats looking at them. An observer who knows the
 *   character's identity uses it, however the body reads.
 */

import { HE, SHE, THEY, type Pronouns } from "./identity";
import { BUST } from "./scale";
import type { Character } from "./character";

/**
 * What an observer can actually make out.
 *
 * The default is the common case: a clothed body seen at conversational
 * distance. Scenes that undress the character, or put them in a crowd at
 * dusk, pass something else.
 */
export interface Visibility {
  /** Whether the body is uncovered. Gates the signals clothing hides. */
  readonly nude: boolean;
  /**
   * Scales every signal: a glimpse in poor light reads less than a
   * face-to-face conversation. 0 means the observer sees nothing useful.
   */
  readonly clarity: number;
}

export const CLOTHED: Visibility = { nude: false, clarity: 1 };
export const NUDE: Visibility = { nude: true, clarity: 1 };
export const GLIMPSED: Visibility = { nude: false, clarity: 0.45 };

/**
 * One readable cue, and how strongly it pushes.
 *
 * `strength` is signed: negative reads masculine, positive feminine. The
 * numbers are deliberately blunt -- this is a legibility model, not a claim
 * about bodies, and every one of them is meant to be tuned by feel once
 * there is content to feel it against.
 */
export interface Signal {
  readonly key: string;
  readonly strength: number;
  readonly visible: boolean;
}

/** Where the bands sit on the -1..+1 axis. */
export const AMBIGUOUS_BELOW = 0.34;

/** What one observer concluded. */
export class Read {
  constructor(
    readonly score: number,
    readonly signals: readonly Signal[] = [],
    /**
     * Set when the observer knows the character and used their identity
     * rather than reading the body at all.
     */
    readonly fromKnowledge = false,
  ) {}

  get ambiguous(): boolean {
    return Math.abs(this.score) < AMBIGUOUS_BELOW;
  }

  get label(): string {
    if (this.ambiguous) return "androgynous";
    return this.score > 0 ? "feminine" : "masculine";
  }

  /** 0 at perfectly ambiguous, 1 at unmistakable. */
  get confidence(): number {
    return Math.min(1, Math.abs(this.score));
  }

  /**
   * The pronouns this read implies.
   *
   * `hedge` decides what an unsure observer does. A narrator hedges; most
   * people guess, and guessing wrong is the interesting outcome, so NPCs
   * should usually pass hedge=false.
   */
  pronouns(hedge = true): Pronouns {
    if (this.ambiguous) {
      if (hedge) return THEY;
      return this.score >= 0 ? SHE : HE;
    }
    return this.score > 0 ? SHE : HE;
  }
}

function signalsFor(character: Character, visibility: Visibility): Signal[] {
  const traits = character.traits;
  const bust = traits.maybe("bust", 0);
  const phallus = traits.maybe("phallus", 0);
  const height = traits.maybe("height", 170);

  // Chest reads through clothing -- less plainly than bare, but a shape is
  // a shape. Scaled across the bands rather than a threshold, so growing
  // changes how you are read gradually.
  let bustStrength = 0.16 * BUST.index(bust);
  if (!visibility.nude) bustStrength *= 0.8;

  // Genitals are a strong signal and almost never a visible one. Gating
  // this is the single most important line in the module.
  const phallusStrength = phallus >= 1 ? -0.55 : 0;

  // Height is a weak, unreliable cue, which is exactly how it should
  // behave: it nudges an ambiguous read and never decides one.
  const midpoint = 172;
  const heightStrength = Math.max(-0.18, Math.min(0.18, (midpoint - height) / 120));

  return [
    { key: "bust", strength: bustStrength, visible: true },
    { key: "phallus", strength: phallusStrength, visible: visibility.nude },
    { key: "height", strength: heightStrength, visible: true },
  ];
}

/** How `character` reads to an observer with this much to go on. */
export function presentation(
  character: Character,
  visibility: Visibility = CLOTHED,
): Read {
  const signals = signalsFor(character, visibility);
  let score = signals
    .filter((signal) => signal.visible)
    .reduce((total, signal) => total + signal.strength, 0);

  // Style, clothing and manner push the read without being body traits.
  // Content sets this; there is no trait behind it on purpose, because a
  // character can change how they dress without changing.
  score += character.presentationBias;

  score = Math.max(-1, Math.min(1, score)) * visibility.clarity;
  return new Read(score, signals);
}

/**
 * What one observer concludes about `character`.
 *
 * An observer who knows them uses their identity, however they read -- that
 * is the whole difference between a stranger and someone who has been told,
 * and it is what makes being known worth something.
 */
export function perceive(
  character: Character,
  visibility: Visibility = CLOTHED,
  options: { knowsIdentity?: boolean } = {},
): Read {
  if (options.knowsIdentity) {
    return new Read(identityScore(character), [], true);
  }
  return presentation(character, visibility);
}

/** A score standing in for a known identity, so Read behaves uniformly. */
function identityScore(character: Character): number {
  const p = character.pronouns;
  if (p === SHE) return 1;
  if (p === HE) return -1;
  return 0;
}
