/** A character: an identity, and a body that can be changed out from under it. */

import { GENDERS, type Gender, type Pronouns } from "./identity";
import { findColour } from "./palette";
import {
  CLOTHED,
  NUDE,
  perceive,
  presentation,
  type Read,
  type Visibility,
} from "./perception";
import { Skills, StatBlock } from "../stats";
import { type Change, type TraitKey, Traits } from "./traits";

export class Character {
  /**
   * Set to override the pronouns the gender would imply. Kept separate so a
   * character can change gender without losing a chosen pronoun set.
   */
  pronounOverride: Pronouns | null = null;

  /**
   * Capability, as opposed to body. A transformation changes traits and must
   * not silently make you better at arguing; when content wants both to move
   * it says so.
   */
  stats = new StatBlock();
  skills = new Skills();

  /** Who they were before they were pulled here. */
  backstoryId: string | null = null;

  /**
   * How clothing, manner and grooming push the read, from -1 (masculine) to
   * +1 (feminine). Not a trait: a character can change how they dress without
   * changing. Content sets it; nothing derives it.
   */
  presentationBias = 0;

  constructor(
    readonly traits: Traits = new Traits(),
    public gender: Gender = GENDERS.nonbinary!,
  ) {}

  // -- identity -----------------------------------------------------------

  get name(): string {
    return this.traits.maybe("name", "someone");
  }

  get pronouns(): Pronouns {
    return this.pronounOverride ?? this.gender.pronouns;
  }

  // -- how others see this character --------------------------------------

  /** What the body reads as, to someone who does not know them. */
  presentation(visibility: Visibility = CLOTHED): Read {
    return presentation(this, visibility);
  }

  /** What one observer concludes. See `perception`. */
  perceivedBy(
    visibility: Visibility = CLOTHED,
    options: { knowsIdentity?: boolean } = {},
  ): Read {
    return perceive(this, visibility, options);
  }

  /**
   * Whether a stranger would land on the character's own pronouns.
   *
   * The state a lot of this game's social content hangs off: false is not a
   * bug, it is a situation.
   */
  get readMatchesIdentity(): boolean {
    return this.presentation().pronouns(false) === this.pronouns;
  }

  // -- body ---------------------------------------------------------------

  get hasBust(): boolean {
    return this.traits.maybe("bust", 0) >= 1;
  }

  /** Zero is a real state, not a missing value: bodies change here. */
  get hasPhallus(): boolean {
    return this.traits.maybe("phallus", 0) >= 1;
  }

  /** A one-line description, for the character bar and for debugging. */
  summary(): string {
    const traits = this.traits;
    const parts = [
      String(Math.trunc(traits.maybe("age", 0))),
      this.gender.label,
      traits.label("height"),
      `${traits.label("hair_colour")} hair`,
      `${traits.label("eye_colour")} eyes`,
    ];
    return `${this.name} — ${parts.join(", ")}`;
  }

  // -- convenience --------------------------------------------------------

  set(key: TraitKey, value: unknown): Change | null {
    return this.traits.set(key, value);
  }

  adjust(key: TraitKey, delta: number): Change | null {
    return this.traits.adjust(key, delta);
  }
}

/** The character a new game starts with, until creation exists. */
export function defaultCharacter(name = "Wanderer"): Character {
  return new Character(
    new Traits({
      name,
      age: 24,
      height: 170,
      hair_colour: findColour("dark brown"),
      eye_colour: findColour("hazel"),
      bust: 0,
      phallus: 0,
    }),
    GENDERS.nonbinary!,
  );
}

export { NUDE, CLOTHED };
